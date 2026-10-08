import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.social_exceptions import (
    ChatWithSelfError,
    MessageNotFoundError,
    NotFriendsError,
    UserBlockedError,
)
from src.social.repository import SocialRepository
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
    Бизнес-логика личных чатов: права доступа, отправка, история, отметки прочтения.
    Наружу отдаёт готовые схемы, ORM-модели не покидают сервис.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SocialRepository(session)

    async def list_chats(self, me: uuid.UUID) -> list[ChatOutputSchema]:
        """Диалоги пользователя: собеседник, последнее сообщение и непрочитанные."""
        last_messages = await self.repo.list_last_messages(me)
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
        self._ensure_not_self(me, peer_id)
        await self._ensure_dialog_access(me, peer_id)

        messages = await self.repo.list_dialog_messages(me, peer_id, limit=limit, before_id=before_id)
        return [MessageOutputSchema.model_validate(message) for message in messages]

    async def send_message(
        self, me: uuid.UUID, peer_id: uuid.UUID, content: str
    ) -> MessageOutputSchema:
        self._ensure_not_self(me, peer_id)
        await self._ensure_dialog_access(me, peer_id)

        message = await self.repo.create_message(me, peer_id, content)
        await self.repo.commit()
        logger.info("Сообщение отправлено: message=%s from=%s to=%s", message.id, me, peer_id)
        # Доставку события по вебсокету подхватывает хаб из ws.py.
        return MessageOutputSchema.model_validate(message)

    async def mark_read(
        self, me: uuid.UUID, peer_id: uuid.UUID, last_read_message_id: uuid.UUID
    ) -> None:
        self._ensure_not_self(me, peer_id)
        await self._ensure_dialog_access(me, peer_id)

        message = await self.repo.get_message(last_read_message_id)
        if message is None or message.receiver_id != me or message.sender_id != peer_id:
            raise MessageNotFoundError("Сообщение не найдено в этом диалоге")

        await self.repo.mark_read(me, peer_id, last_read_message_id)
        await self.repo.commit()
        logger.info("Отметка прочтения: user=%s peer=%s up_to=%s", me, peer_id, last_read_message_id)

    async def issue_ws_ticket(self, me: uuid.UUID) -> WsTicketSchema:
        ticket = create_ticket(me)
        return WsTicketSchema(ticket=ticket, expires_in=TICKET_TTL_SECONDS)

    # == Внутренние проверки ==

    @staticmethod
    def _ensure_not_self(me: uuid.UUID, peer_id: uuid.UUID) -> None:
        if me == peer_id:
            raise ChatWithSelfError("Нельзя вести переписку с самим собой")

    async def _ensure_dialog_access(self, me: uuid.UUID, peer_id: uuid.UUID) -> None:
        if await self.repo.is_blocked_between(me, peer_id):
            raise UserBlockedError("Переписка недоступна: пользователь заблокирован")
        if not await self.repo.are_friends(me, peer_id):
            raise NotFriendsError("Переписка доступна только друзьям")
