import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.social_exceptions import (
    ChatWithSelfError,
    NotFriendsError,
    UserBlockedError,
)
from src.social.repository import MessagesRepository
from src.social.schemas import (
    ChatOutputSchema,
    ChatPeerSchema,
    MessageOutputSchema,
    WsTicketSchema,
)
from src.social.tickets import TICKET_TTL_SECONDS, create_ticket

logger = logging.getLogger(__name__)


class SocialService:
    """
    Бизнес-логика личных чатов: проверки доступа, отправка, история, отметки прочтения.
    Наружу отдаёт готовые схемы, ORM-модели не покидают сервис.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = MessagesRepository(session)

    async def list_chats(self, me: uuid.UUID) -> list[ChatOutputSchema]:
        """Диалоги пользователя: собеседник, последнее сообщение и число непрочитанных."""
        last_messages = await self.repo.get_last_messages(me)
        unread_by_peer = await self.repo.count_unread_by_peers(me)
        users = await self.repo.get_users({peer_id for _, peer_id in last_messages})

        chats: list[ChatOutputSchema] = []
        for message, peer_id in last_messages:
            peer = users.get(peer_id)
            if peer is None:
                continue
            chats.append(
                ChatOutputSchema(
                    peer=ChatPeerSchema.model_validate(peer),
                    last_message_id=message.id,
                    last_message_text=message.content,
                    last_message_at=message.created_at,
                    unread_count=unread_by_peer.get(peer_id, 0),
                )
            )
        return chats

    async def history(
        self,
        me: uuid.UUID,
        peer_id: uuid.UUID,
        limit: int = 50,
        before_id: uuid.UUID | None = None,
    ) -> list[MessageOutputSchema]:
        """История диалога, свежие первыми; before_id — курсор для листания вверх."""
        await self._ensure_dialog_access(me, peer_id)
        messages = await self.repo.get_dialog(me, peer_id, limit=limit, before_id=before_id)
        return [MessageOutputSchema.model_validate(message) for message in messages]

    async def send_message(
        self, me: uuid.UUID, receiver_id: uuid.UUID, content: str
    ) -> MessageOutputSchema:
        await self._ensure_dialog_access(me, receiver_id)
        message = await self.repo.create_message(me, receiver_id, content)
        logger.info("Сообщение отправлено: message=%s from=%s to=%s", message.id, me, receiver_id)
        return MessageOutputSchema.model_validate(message)

    async def mark_read(
        self, me: uuid.UUID, message_ids: list[uuid.UUID]
    ) -> list[MessageOutputSchema]:
        """
        Помечает прочитанными переданные сообщения.
        Репозиторий сам отфильтрует те, что адресованы не мне, поэтому чужие не пострадают.
        """
        messages = await self.repo.mark_messages_read(message_ids, reader_id=me)
        logger.info("Отметка прочтения: user=%s сообщений=%s", me, len(messages))
        return [MessageOutputSchema.model_validate(message) for message in messages]

    async def issue_ws_ticket(self, me: uuid.UUID) -> WsTicketSchema:
        ticket = await create_ticket(me)
        return WsTicketSchema(ticket=ticket, expires_in=TICKET_TTL_SECONDS)

    # == Внутренние проверки ==

    async def _ensure_dialog_access(self, me: uuid.UUID, peer_id: uuid.UUID) -> None:
        if me == peer_id:
            raise ChatWithSelfError("Нельзя вести переписку с самим собой")
        if await self.repo.is_blocked_between(me, peer_id):
            raise UserBlockedError("Переписка недоступна: пользователь заблокирован")
        if not await self.repo.are_friends(me, peer_id):
            raise NotFriendsError("Переписка доступна только друзьям")
