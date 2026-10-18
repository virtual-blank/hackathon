import uuid
from datetime import date

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.feed.models import Review
from src.habits.enums import InviteStatus, Visibility
from src.habits.models import Habit, HabitLog, SharedHabitUser
from src.users.models import UserAchievement


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_habits_with_shared(
        self,
        user_id: uuid.UUID,
        visibilities: list[Visibility] | None = None,
    ) -> list[tuple[Habit, bool]]:
        stmt = (
            select(
                Habit,
                SharedHabitUser.id.is_not(None).label("is_shared"),
            )
            .outerjoin(
                SharedHabitUser,
                (SharedHabitUser.habit_id == Habit.id) & (SharedHabitUser.status == InviteStatus.ACCEPTED),
            )
            .where(
                or_(
                    Habit.creator_id == user_id,
                    SharedHabitUser.user_id == user_id,
                )
            )
        )
        if visibilities is not None:
            stmt = stmt.where(Habit.visibility.in_(visibilities))

        stmt = stmt.order_by(Habit.created_at.desc())
        result = await self.session.execute(stmt)
        return [(row[0], bool(row[1])) for row in result.all()]

    async def get_user_logs_dates_by_habit(
        self, user_id: uuid.UUID, habit_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[date]]:
        if not habit_ids:
            return {}

        stmt = (
            select(HabitLog.habit_id, HabitLog.completed_date)
            .where(
                HabitLog.user_id == user_id,
                HabitLog.habit_id.in_(habit_ids),
            )
            .order_by(HabitLog.completed_date.asc())
        )
        result = await self.session.execute(stmt)
        logs_map: dict[uuid.UUID, list[date]] = {h_id: [] for h_id in habit_ids}
        for habit_id, completed_date in result.all():
            logs_map.setdefault(habit_id, []).append(completed_date)
        return logs_map

    async def get_reviews_counts_by_habit(self, habit_ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[int, int]]:
        if not habit_ids:
            return {}

        stmt = (
            select(
                Review.habit_id,
                func.coalesce(func.sum(case((Review.rate == 1, 1), else_=0)), 0).label("pushes"),
                func.coalesce(func.sum(case((Review.rate == 0, 1), else_=0)), 0).label("shames"),
            )
            .where(Review.habit_id.in_(habit_ids))
            .group_by(Review.habit_id)
        )
        result = await self.session.execute(stmt)
        return {row.habit_id: (int(row.pushes), int(row.shames)) for row in result.all()}

    async def get_achievements_count(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(UserAchievement.id)).where(UserAchievement.user_id == user_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one_or_none() or 0)
