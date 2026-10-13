import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.friends.models import UserRelation
from src.social.enums import RelationStatus
from src.users.models import User


class FriendsRepository:
    """Не коммитит сам: транзакцию закрывает сервис, чтобы операция из нескольких шагов была атомарной."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pair_relations(self, first_id: uuid.UUID, second_id: uuid.UUID) -> list[UserRelation]:
        """Все строки между двумя пользователями в обе стороны."""
        stmt = select(UserRelation).where(
            or_(
                and_(UserRelation.user_id == first_id, UserRelation.target_id == second_id),
                and_(UserRelation.user_id == second_id, UserRelation.target_id == first_id),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def add_relation(self, user_id: uuid.UUID, target_id: uuid.UUID, status: RelationStatus) -> None:
        self.session.add(UserRelation(user_id=user_id, target_id=target_id, status=status))

    async def delete_relation(self, relation: UserRelation) -> None:
        await self.session.delete(relation)

    async def get_friends(self, user_id: uuid.UUID, limit: int, offset: int) -> list[User]:
        # Строка дружбы направленная, поэтому друг может стоять с любой её стороны.
        stmt = (
            select(User)
            .join(
                UserRelation,
                or_(
                    and_(UserRelation.user_id == user_id, UserRelation.target_id == User.id),
                    and_(UserRelation.target_id == user_id, UserRelation.user_id == User.id),
                ),
            )
            .where(UserRelation.status == RelationStatus.ACCEPTED)
            .order_by(User.username)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_incoming_requests(self, user_id: uuid.UUID, limit: int) -> list[User]:
        """Пользователи, которые отправили заявку user_id; новые заявки первыми."""
        stmt = (
            select(User)
            .join(UserRelation, UserRelation.user_id == User.id)
            .where(UserRelation.target_id == user_id, UserRelation.status == RelationStatus.PENDING)
            .order_by(UserRelation.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_outgoing_requests(self, user_id: uuid.UUID, limit: int) -> list[User]:
        """Пользователи, которым user_id отправил заявку; новые заявки первыми."""
        stmt = (
            select(User)
            .join(UserRelation, UserRelation.target_id == User.id)
            .where(UserRelation.user_id == user_id, UserRelation.status == RelationStatus.PENDING)
            .order_by(UserRelation.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
