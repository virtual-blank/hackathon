import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from src.habits.models import Habit
from src.habits.repository import HabitLogRepository, HabitsRepository
from src.habits.schemas import (
    HabitCreateSchema,
    HabitOutputSchema,
    HabitUpdateSchema,
    MarkedHabitOutputSchema,
)
from src.users.models import User


class HabitsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.habit_repo = HabitsRepository(session=session)
        self.habit_log_repo = HabitLogRepository(session=session)

    async def create_habit(self, user_id: uuid.UUID, habit_data: HabitCreateSchema):
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        start_date = datetime.now(ZoneInfo(user.timezone)).date()
        habit = await self.habit_repo.create_habit(
            creator_id=user_id,
            title=habit_data.title,
            color_hex=habit_data.color_hex,
            visibility=habit_data.visibility,
            start_date=start_date,
            notification_times=habit_data.notification_times,
        )
        return HabitOutputSchema.model_validate(habit)

    async def get_habit(self, user_id: uuid.UUID, habit_id: uuid.UUID):
        habit = await self.habit_repo.get_habit_by_id(habit_id=habit_id, creator_id=user_id)
        if habit is None:
            return None
        return HabitOutputSchema.model_validate(habit)

    async def get_habits(self, user_id: uuid.UUID):
        habits = await self.habit_repo.get_all_habits(creator_id=user_id)
        return [HabitOutputSchema.model_validate(habit) for habit in habits]

    async def update_habit(self, user_id: uuid.UUID, habit_id: uuid.UUID, habit_data: HabitUpdateSchema):
        updates = habit_data.model_dump(exclude_unset=True)
        if not updates:
            raise ValueError("Необходимо указать хотя бы одно поле для обновления")
        if any(value is None for value in updates.values()):
            raise ValueError("Значение None для полей не допустимо")

        habit = await self.habit_repo.update_habit(habit_id=habit_id, creator_id=user_id, updates=updates)
        if habit is None:
            return None

        return HabitOutputSchema.model_validate(habit)

    async def delete_habit(self, user_id: uuid.UUID, habit_id: uuid.UUID):
        return await self.habit_repo.delete_habit(habit_id=habit_id, creator_id=user_id)

    async def mark_habit(self, habit_id: uuid.UUID, current_user: User):

        habit = await self.session.get(Habit, habit_id)
        if not habit:
            raise ValueError("Привычка не найдена")

        tz = ZoneInfo(current_user.timezone)
        today_date = datetime.now(tz).date()
        yesterday_date = today_date - timedelta(days=1)

        new_log_dao = await self.habit_log_repo.mark_completed(
            user_id=current_user.id, habit_id=habit_id, completed_date=today_date
        )

        yesterday_logs = await self.habit_log_repo.get_logs_in_range(
            user_id=current_user.id, date_from=yesterday_date, date_to=yesterday_date, habit_id=habit_id
        )
        if not yesterday_logs:
            new_streak = 1
        else:
            new_streak = habit.current_streak_days + 1

        new_max_streak = max(habit.max_streak_days, new_streak)

        updated_habit_dao = await self.habit_repo.update_habit(
            habit_id=habit_id,
            creator_id=habit.creator_id,
            updates={"current_streak_days": new_streak, "max_streak_days": new_max_streak},
        )
        return MarkedHabitOutputSchema(log=new_log_dao, habit=updated_habit_dao)
