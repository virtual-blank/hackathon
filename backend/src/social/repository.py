import uuid

from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.social.enums import RelationStatus
from src.social.models import Message, UserRelation
from src.users.models import User


class SocialRepository:
    """Только запросы к БД. Бизнес-правила живут в сервисе."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _dialog_filter(me: uuid.UUID, peer_id: uuid.UUID):
        """Переписка двусторонняя: сообщения в обе стороны."""
        return or_(
            and_(Message.sender_id == me, Message.receiver_id == peer_id),
            and_(Message.sender_id == peer_id, Message.receiver_id == me),
        )

    # == Пользователи ==

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_users(self, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, User]:
        if not user_ids:
            return {}
        stmt = select(User).where(User.id.in_(user_ids))
        users = (await self.session.scalars(stmt)).all()
        return {user.id: user for user in users}

    # == Сообщения ==

    async def list_dialog_messages(
        self,
        me: uuid.UUID,
        peer_id: uuid.UUID,
        limit: int = 50,
        before_id: uuid.UUID | None = None,
    ) -> list[Message]:
        """История диалога: свежие первыми, before_id — курсор для листания вверх."""
        stmt = (
            select(Message)
            .where(self._dialog_filter(me, peer_id))
            .order_by(Message.id.desc())
            .limit(limit)
        )
        if before_id is not None:
            stmt = stmt.where(Message.id < before_id)
        return list((await self.session.scalars(stmt)).all())

    async def list_last_messages(self, me: uuid.UUID) -> list[tuple[Message, uuid.UUID]]:
        """
        Последнее сообщение по каждому собеседнику — для списка диалогов.
        Нумерация внутри собеседника через оконную функцию: одного запроса достаточно,
        отдельный запрос на каждый диалог не нужен.
        """
        peer_expr = case((Message.sender_id == me, Message.receiver_id), else_=Message.sender_id)
        ranked = (
            select(
                Message.id.label("message_id"),
                peer_expr.label("peer_id"),
                func.row_number()
                .over(partition_by=peer_expr, order_by=Message.id.desc())
                .label("row_number"),
            )
            .where(or_(Message.sender_id == me, Message.receiver_id == me))
            .subquery()
        )
        stmt = (
            select(Message, ranked.c.peer_id)
            .join(ranked, ranked.c.message_id == Message.id)
            .where(ranked.c.row_number == 1)
            .order_by(Message.id.desc())
        )
        rows = (await self.session.execute(stmt)).all()
        return [(message, peer_id) for message, peer_id in rows]

    async def get_message(self, message_id: uuid.UUID) -> Message | None:
        return await self.session.get(Message, message_id)

    async def create_message(
        self, sender_id: uuid.UUID, receiver_id: uuid.UUID, content: str
    ) -> Message:
        message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
        self.session.add(message)
        await self.session.flush()
        # created_at и is_read задаются на стороне БД, подтягиваем их явно.
        await self.session.refresh(message)
        return message

    # == Прочитано / непрочитано ==

    async def mark_read(
        self, me: uuid.UUID, peer_id: uuid.UUID, up_to_message_id: uuid.UUID
    ) -> None:
        """Помечаем прочитанным всё, что пришло от собеседника до указанного сообщения."""
        await self.session.execute(
            update(Message)
            .where(
                Message.receiver_id == me,
                Message.sender_id == peer_id,
                Message.id <= up_to_message_id,
                Message.is_read.is_(False),
            )
            .values(is_read=True, read_at=func.now())
        )

    async def count_unread(self, me: uuid.UUID, peer_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Message)
            .where(
                Message.receiver_id == me,
                Message.sender_id == peer_id,
                Message.is_read.is_(False),
            )
        )
        return (await self.session.scalar(stmt)) or 0

    async def count_unread_by_peers(self, me: uuid.UUID) -> dict[uuid.UUID, int]:
        """Непрочитанные по всем собеседникам одним запросом."""
        stmt = (
            select(Message.sender_id, func.count())
            .where(Message.receiver_id == me, Message.is_read.is_(False))
            .group_by(Message.sender_id)
        )
        rows = (await self.session.execute(stmt)).all()
        return {peer_id: count for peer_id, count in rows}

    # == Отношения пользователей ==

    async def are_friends(self, user_a: uuid.UUID, user_b: uuid.UUID) -> bool:
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

    # == Транзакция ==

    async def commit(self) -> None:
        await self.session.commit()
