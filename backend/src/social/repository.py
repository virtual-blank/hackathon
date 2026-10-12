import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.social.enums import RelationStatus
from src.social.models import Message, UserRelation
from src.users.models import User


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

    # == Список диалогов ==

    async def get_last_messages(self, user_id: uuid.UUID) -> list[tuple[Message, uuid.UUID]]:
        """
        Последнее сообщение по каждому собеседнику — для списка диалогов.
        Нумерация внутри собеседника оконной функцией: одного запроса достаточно,
        обходить диалоги по одному не нужно.
        """
        peer_expr = case(
            (Message.sender_id == user_id, Message.receiver_id), else_=Message.sender_id
        )
        ranked = (
            select(
                Message.id.label("message_id"),
                peer_expr.label("peer_id"),
                func.row_number()
                .over(partition_by=peer_expr, order_by=Message.id.desc())
                .label("row_number"),
            )
            .where(or_(Message.sender_id == user_id, Message.receiver_id == user_id))
            .subquery()
        )
        stmt = (
            select(Message, ranked.c.peer_id)
            .join(ranked, ranked.c.message_id == Message.id)
            .where(ranked.c.row_number == 1)
            .order_by(Message.id.desc())
        )
        result = await self.session.execute(stmt)
        return [(message, peer_id) for message, peer_id in result.all()]

    async def count_unread_by_peers(self, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
        """Количество непрочитанных по каждому собеседнику — одним запросом."""
        stmt = (
            select(Message.sender_id, func.count())
            .where(Message.receiver_id == user_id, Message.is_read.is_(False))
            .group_by(Message.sender_id)
        )
        result = await self.session.execute(stmt)
        return {peer_id: count for peer_id, count in result.all()}

    # == Пользователи ==

    async def get_users(self, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, User]:
        """Пользователи по списку id — чтобы не ходить в БД на каждый диалог."""
        if not user_ids:
            return {}
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.session.execute(stmt)
        return {user.id: user for user in result.scalars().all()}

    # == Отношения пользователей ==

    async def are_friends(self, user_a: uuid.UUID, user_b: uuid.UUID) -> bool:
        """Дружба — статус accepted, направление записи не важно."""
        stmt = (
            select(UserRelation.id)
            .where(
                UserRelation.status == RelationStatus.ACCEPTED,
                or_(
                    and_(UserRelation.user_id == user_a, UserRelation.target_id == user_b),
                    and_(UserRelation.user_id == user_b, UserRelation.target_id == user_a),
                ),
            )
            .limit(1)
        )
        return (await self.session.scalar(stmt)) is not None

    async def is_blocked_between(self, user_a: uuid.UUID, user_b: uuid.UUID) -> bool:
        """Блокировка в любую сторону закрывает переписку обоим."""
        stmt = (
            select(UserRelation.id)
            .where(
                UserRelation.status == RelationStatus.BLOCKED,
                or_(
                    and_(UserRelation.user_id == user_a, UserRelation.target_id == user_b),
                    and_(UserRelation.user_id == user_b, UserRelation.target_id == user_a),
                ),
            )
            .limit(1)
        )
        return (await self.session.scalar(stmt)) is not None