import uuid
from datetime import date, timedelta

from sqlalchemy import case, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from src.feed.models import Review
from src.habits.enums import Visibility
from src.habits.models import Habit, HabitLog
from src.social.enums import RelationStatus
from src.social.models import UserRelation
from src.users.models import User


class FeedRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _commit(self):
        await self.session.commit()

    async def _rollback(self):
        await self.session.rollback()

    async def get_friends_feed(self, user_id: uuid.UUID, limit: int, offset: int):

        # запрос кентов
        friends_stmt = select(
            case((UserRelation.user_id == user_id, UserRelation.target_id), else_=UserRelation.user_id)
        ).where(
            UserRelation.status == RelationStatus.ACCEPTED,
            or_(UserRelation.user_id == user_id, UserRelation.target_id == user_id),
        )

        # подзапрос для последней активности и кол-ва логов
        latest_activity_stmt = (
            select(
                HabitLog.habit_id,
                func.max(HabitLog.completed_date).label("last_log_date"),
                func.count(HabitLog.id).label("total_logs_count"),
            ).group_by(HabitLog.habit_id)
        ).subquery()

        ninety_days_ago = date.today() - timedelta(days=90)

        # мейн запрос
        stmt = (
            select(Habit, latest_activity_stmt.c.total_logs_count)
            .join(latest_activity_stmt, Habit.id == latest_activity_stmt.c.habit_id)
            .where(Habit.creator_id.in_(friends_stmt), Habit.visibility != Visibility.PRIVATE)
            .order_by(latest_activity_stmt.c.last_log_date.desc())
            .limit(limit)
            .offset(offset)
            .options(
                # берем логи только за последние 90 дней (чтобы фронтенд )
                selectinload(Habit.logs.and_(HabitLog.completed_date >= ninety_days_ago)),
                # берет реакции к привычке и джоиним авторов
                selectinload(Habit.reviews).joinedload(Review.reviewer),
            )
        )

        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def create_review_and_get_reviewer(
        self, reviewer_id: uuid.UUID, habit_id: uuid.UUID, comment: str | None, rate: int
    ) -> Review:
        new_review = Review(reviewer_id=reviewer_id, habit_id=habit_id, comment=comment, rate=rate)
        self.session.add(new_review)
        await self._commit()

        stmt = select(Review).where(Review.id == new_review.id).options(joinedload(Review.reviewer))
        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def get_reviewer(self, user_id: uuid.UUID):
        stmt = select(User.id, User.username).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def edit_review(
        self, review_id: uuid.UUID, reviewer_id: uuid.UUID, habit_id: uuid.UUID, new_review_dict: dict
    ) -> bool:
        stmt = (
            update(Review)
            .where(Review.id == review_id, Review.reviewer_id == reviewer_id, Review.habit_id == habit_id)
            .values(**new_review_dict)
            .returning(Review.id)
        )
        result = await self.session.execute(stmt)
        updated_review_id = result.scalar_one_or_none()
        if not updated_review_id:
            await self.session.rollback()
            return False
        await self._commit()
        return True

    async def delete_review(self, reviewer_id: uuid.UUID, review_id: uuid.UUID) -> bool:
        stmt = delete(Review).where(Review.id == review_id, Review.reviewer_id == reviewer_id).returning(Review.id)
        result = await self.session.execute(stmt)
        deleted_id = result.scalar_one_or_none()
        if not deleted_id:
            return False
        await self._commit()
        return True
