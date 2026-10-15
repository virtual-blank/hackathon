import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from src.friends.repository import FriendsRepository
from src.habits.enums import Visibility
from src.habits.models import Habit
from src.habits.repository import HabitLogRepository, HabitsRepository
from src.habits.schemas import (
    HabitCreateSchema,
    HabitLogOutputSchema,
    HabitOutputSchema,
    HabitUpdateSchema,
    MarkedHabitOutputSchema,
)
from src.social.enums import RelationStatus
from src.users.models import User

class HabitLogService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = HabitLogRepository(session=session)

    async def mark_completed(self, user_id: uuid.UUID, habit_id: uuid.UUID, completed_date: date | None = None):
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        if not user.timezone:
            raise ValueError("Часовой пояс пользователя не указан")

        try:
            user_timezone = ZoneInfo(user.timezone)
        except ZoneInfoNotFoundError:
            raise ValueError("Некорректный часовой пояс пользователя")

        date_today = datetime.now(user_timezone).date()

        if completed_date is None:
            completed_date = date_today

        if completed_date > date_today:
            raise ValueError("Нельзя отметить привычку выполненной в будущем")

        log = await self.repo.mark_completed(user_id=user_id, habit_id=habit_id, completed_date=completed_date)
        return HabitLogOutputSchema.model_validate(log)

    async def get_logs_in_range(
            self,
            user_id: uuid.UUID,
            date_from: date,
            date_to: date,
            habit_id: uuid.UUID | None = None,
            limit: int = 50,
            offset: int = 0,
    ):
        logs = await self.repo.get_logs_in_range(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            habit_id=habit_id,
            limit=limit,
            offset=offset,
        )
        return [HabitLogOutputSchema.model_validate(log) for log in logs]


    async def get_completed_habits_by_date(self, user_id: uuid.UUID, target_date: date):
        completed_habits = await self.repo.get_completed_habits_by_date(user_id=user_id, target_date=target_date)
        return [HabitOutputSchema.model_validate(completed_habit) for completed_habit in completed_habits]


    async def get_uncompleted_habits_by_date(self, user_id: uuid.UUID, target_date: date):
        uncompleted_habits = await self.repo.get_uncompleted_habits_by_date(user_id=user_id, target_date=target_date)
        return [HabitOutputSchema.model_validate(uncompleted_habit) for uncompleted_habit in uncompleted_habits]

    # async def delete_log(self, user_id: uuid.UUID, log_id: uuid.UUID):
    #     return await self.repo.delete_log(user_id=user_id, log_id=log_id)

    # async def remove_completion(self, user_id: uuid.UUID, habit_id: uuid.UUID, completed_date: date | None = None):
    #     user = await self.session.get(User, user_id)
    #     if user is None:
    #         raise ValueError("Пользователь не найден")
    #     if not user.timezone:
    #         raise ValueError("Часовой пояс пользователя не указан")
    #
    #     try:
    #         user_timezone = ZoneInfo(user.timezone)
    #     except ZoneInfoNotFoundError:
    #         raise ValueError("Некорректный часовой пояс пользователя")
    #
    #     date_today = datetime.now(user_timezone).date()
    #     if completed_date is None:
    #         completed_date = date_today
    #
    #     log = await self.repo.remove_completion(user_id=user_id, habit_id=habit_id, completed_date=completed_date)
    #     return log


class HabitsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.habit_repo = HabitsRepository(session=session)
        self.habit_log_repo = HabitLogRepository(session=session)
        self.friends_repo = FriendsRepository(session=session)

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

    async def get_habits(
            self,
            user_id: uuid.UUID,
            visibility: list[Visibility] | None = None,
            target_user_id: uuid.UUID | None = None,
            start_date: date | None = None,
            end_date: date | None = None,
            status: str | None = None,
            limit: int = 50,
            offset: int = 0,
    ):
        if target_user_id is None or target_user_id == user_id:
            target_user_id = user_id
        else:
            relations = await self.friends_repo.get_pair_relations(first_id=user_id, second_id=target_user_id)
            is_friend = any(relation.status == RelationStatus.ACCEPTED for relation in relations)
            is_blocked = any(
                relation.status == RelationStatus.BLOCKED
                and relation.user_id == target_user_id
                and relation.target_id == user_id
                for relation in relations
            )

            if is_blocked:
                raise ValueError("Доступ к привычкам пользователя запрещён")

            if is_friend:
                visibility = [Visibility.FRIENDS, Visibility.PUBLIC]
            else:
                visibility = [Visibility.PUBLIC]

        habits = await self.habit_repo.get_all_habits(
            creator_id=target_user_id,
            visibility=visibility,
            start_date=start_date,
            end_date=end_date,
            status=status,
            limit=limit,
            offset=offset,
        )
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

