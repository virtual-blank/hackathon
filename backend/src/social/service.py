import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.social.enums import RelationStatus
from src.social.models import Message, UserRelation
from src.social.repository import MessagesRepository


class SocialService:
    """Бизнес-логика чата между пользователями."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MessagesRepository(session=session)

    async def send_message(
        self,
        sender_id: uuid.UUID,
        receiver_id: uuid.UUID,
        content: str,
    ) -> Message:
        """
        Отправить сообщение.
        Проверки: не сам себе, нет блокировки, получатель существует (через FK).
        """
        if sender_id == receiver_id:
            raise ValueError("Нельзя отправить сообщение самому себе")

        if await self._is_blocked(sender_id, receiver_id):
            raise ValueError("Невозможно отправить сообщение: пользователь недоступен")

        try:
            return await self.repo.create_message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
            )
        except IntegrityError as exc:
            if "receiver_id" in str(exc.orig):
                raise ValueError("Пользователь не найден") from exc
            raise

    async def get_history(
        self,
        user_id: uuid.UUID,
        peer_id: uuid.UUID,
        limit: int = 50,
        before_id: uuid.UUID | None = None,
    ) -> list[Message]:
        """История сообщений между двумя пользователями."""
        if user_id == peer_id:
            raise ValueError("Нельзя запросить переписку с самим собой")

        return await self.repo.get_dialog(
            user1_id=user_id,
            user2_id=peer_id,
            limit=limit,
            before_id=before_id,
        )

    async def mark_as_read(
        self,
        message_ids: list[uuid.UUID],
        reader_id: uuid.UUID,
    ) -> list[Message]:
        """Пометить сообщения прочитанными. Только полученные reader_id."""
        return await self.repo.mark_messages_read(
            message_ids=message_ids,
            reader_id=reader_id,
        )

    async def get_unread(
        self,
        user_id: uuid.UUID,
        from_user_id: uuid.UUID,
    ) -> list[Message]:
        """Непрочитанные сообщения от конкретного пользователя."""
        return await self.repo.get_unread(
            user_id=user_id,
            from_user_id=from_user_id,
        )

    async def _is_blocked(
        self,
        user_a: uuid.UUID,
        user_b: uuid.UUID,
    ) -> bool:
        """
        Проверить, есть ли блокировка в любую сторону между двумя пользователями.
        Если A заблокировал B или B заблокировал A — сообщение запрещено.
        """
        stmt = select(UserRelation).where(
            UserRelation.status == RelationStatus.BLOCKED,
            ((UserRelation.user_id == user_a) & (UserRelation.target_id == user_b))
            | ((UserRelation.user_id == user_b) & (UserRelation.target_id == user_a)),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
