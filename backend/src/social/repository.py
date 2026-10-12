import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.social.models import Message


class MessagesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_message(
        self,
        sender_id: uuid.UUID,
        receiver_id: uuid.UUID,
        content: str,
    ) -> Message:
        """Создать новое сообщение."""
        new_message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
        )
        self.session.add(new_message)
        await self.session.commit()
        await self.session.refresh(new_message)
        return new_message

    async def get_dialog(
        self,
        user1_id: uuid.UUID,
        user2_id: uuid.UUID,
        limit: int = 50,
        before_id: uuid.UUID | None = None,
    ) -> list[Message]:
        """
        История сообщений между двумя пользователями (в обе стороны).
        Сортировка — по id (UUIDv7 растёт со временем).
        Пагинация — курсорная: всё «до» before_id (для скролла вверх).
        """
        stmt = select(Message).where(
            or_(
                and_(Message.sender_id == user1_id, Message.receiver_id == user2_id),
                and_(Message.sender_id == user2_id, Message.receiver_id == user1_id),
            )
        )
        if before_id is not None:
            stmt = stmt.where(Message.id < before_id)
        stmt = stmt.order_by(Message.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_messages_read(
        self,
        message_ids: list[uuid.UUID],
        reader_id: uuid.UUID,
    ) -> list[Message]:
        """
        Пометить сообщения прочитанными.
        Только те, где receiver_id = reader_id (нельзя пометить чужие).
        """
        stmt = (
            update(Message)
            .where(
                Message.id.in_(message_ids),
                Message.receiver_id == reader_id,
                Message.is_read.is_(False),
            )
            .values(is_read=True, read_at=datetime.now(timezone.utc))
            .returning(Message)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return list(result.scalars().all())

    async def get_unread(
        self,
        user_id: uuid.UUID,
        from_user_id: uuid.UUID,
    ) -> list[Message]:
        """Все непрочитанные сообщения от конкретного пользователя."""
        stmt = (
            select(Message)
            .where(
                Message.receiver_id == user_id,
                Message.sender_id == from_user_id,
                Message.is_read.is_(False),
            )
            .order_by(Message.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
