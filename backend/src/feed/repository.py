import uuid
from datetime import date, timedelta

from sqlalchemy import and_, case, delete, exists, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.feed.models import Review
from src.habits.enums import Visibility
from src.habits.models import Habit, HabitLog
from src.social.enums import RelationStatus
from src.social.models import UserRelation


class FeedRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _commit(self):
        await self.session.commit()

    async def _rollback(self):
        await self.session.rollback()

    async def get_friends_feed(self, user_id: uuid.UUID, limit: int, offset: int):
        # id всех друзей
        friends_stmt = select(
            case((UserRelation.user_id == user_id, UserRelation.target_id), else_=UserRelation.user_id)
        ).where(
            UserRelation.status == RelationStatus.ACCEPTED,
            or_(UserRelation.user_id == user_id, UserRelation.target_id == user_id),
        )

        # последняя активность, общее количество логов
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
            select(
                Habit,
                func.coalesce(latest_activity_stmt.c.total_logs_count, 0).label("total_logs_count"),
            )
            .outerjoin(latest_activity_stmt, Habit.id == latest_activity_stmt.c.habit_id)
            .where(Habit.creator_id.in_(friends_stmt), Habit.visibility != Visibility.PRIVATE)
            .order_by(
                func.coalesce(latest_activity_stmt.c.last_log_date, Habit.start_date).desc(),
                Habit.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
            .options(
                joinedload(Habit.creator),
                selectinload(Habit.logs.and_(HabitLog.completed_date >= ninety_days_ago)),
                selectinload(Habit.reviews).joinedload(Review.reviewer),
            )
        )

        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.unique().all()]

    async def can_user_review_habit(self, user_id: uuid.UUID, habit_id: uuid.UUID) -> None:
        habit = await self.session.get(Habit, habit_id)
        if habit is None or habit.visibility == Visibility.PRIVATE:
            raise ValueError("Привычка не найдена или скрыта")

        if habit.creator_id == user_id:
            raise ValueError("Нельзя оценивать собственную привычку")

        friend_exists_stmt = select(
            exists().where(
                UserRelation.status == RelationStatus.ACCEPTED,
                or_(
                    and_(UserRelation.user_id == user_id, UserRelation.target_id == habit.creator_id),
                    and_(UserRelation.user_id == habit.creator_id, UserRelation.target_id == user_id),
                ),
            )
        )
        is_friend = (await self.session.execute(friend_exists_stmt)).scalar()
        if not is_friend:
            raise ValueError("Оценивать можно только привычки друзей")

    async def create_review_and_get_reviewer(
        self, reviewer_id: uuid.UUID, habit_id: uuid.UUID, comment: str | None, rate: int
    ) -> Review:
        new_review = Review(reviewer_id=reviewer_id, habit_id=habit_id, comment=comment, rate=rate)
        self.session.add(new_review)
        try:
            await self._commit()
        except IntegrityError as exc:
            await self._rollback()
            raise ValueError("Вы уже оставляли реакцию на эту привычку") from exc

        stmt = select(Review).where(Review.id == new_review.id).options(joinedload(Review.reviewer))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def edit_review(self, review_id: uuid.UUID, reviewer_id: uuid.UUID, new_review_dict: dict) -> Review | None:
        stmt = (
            update(Review)
            .where(Review.id == review_id, Review.reviewer_id == reviewer_id)
            .values(**new_review_dict)
            .returning(Review.id)
        )
        result = await self.session.execute(stmt)
        updated_review_id = result.scalar_one_or_none()
        if not updated_review_id:
            await self._rollback()
            return None

        await self._commit()
        select_stmt = select(Review).where(Review.id == updated_review_id).options(joinedload(Review.reviewer))
        return (await self.session.execute(select_stmt)).scalar_one()

    async def delete_review(self, reviewer_id: uuid.UUID, review_id: uuid.UUID) -> bool:
        stmt = delete(Review).where(Review.id == review_id, Review.reviewer_id == reviewer_id).returning(Review.id)
        result = await self.session.execute(stmt)
        deleted_id = result.scalar_one_or_none()
        if not deleted_id:
            await self._rollback()
            return False
        await self._commit()
        return True
