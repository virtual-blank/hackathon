import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from src.habits.repository import HabitsRepository
from src.habits.schemas import HabitCreateSchema, HabitOutputSchema, HabitUpdateSchema
from src.users.models import User


class HabitsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = HabitsRepository(session=session)

    async def create_habit(self, user_id: uuid.UUID,  habit_data: HabitCreateSchema):
        user = await self.session.get(User, user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        start_date = datetime.now(ZoneInfo(user.timezone)).date()
        habit = await self.repo.create_habit(
            creator_id=user_id,
            title=habit_data.title,
            color_hex=habit_data.color_hex,
            visibility=habit_data.visibility,
            start_date=start_date,
            notification_times=habit_data.notification_times,
        )
        return HabitOutputSchema.model_validate(habit)

    async def get_habit(self, user_id: uuid.UUID, habit_id: uuid.UUID):
        habit = await self.repo.get_habit_by_id(habit_id=habit_id, creator_id=user_id)
        if habit is None:
            return None
        return HabitOutputSchema.model_validate(habit)

    async def get_habits(self, user_id: uuid.UUID):
        habits = await self.repo.get_all_habits(creator_id=user_id)
        return [HabitOutputSchema.model_validate(habit) for habit in habits]

    async def update_habit(self, user_id: uuid.UUID, habit_id: uuid.UUID, habit_data: HabitUpdateSchema):
        updates = habit_data.model_dump(exclude_unset=True)
        if not updates:
            raise ValueError("Необходимо указать хотя бы одно поле для обновления")
        if any(value is None for value in updates.values()):
            raise ValueError("Значение None для полей не допустимо")

        habit = await self.repo.update_habit(habit_id=habit_id, creator_id=user_id, updates=updates)
        if habit is None:
            return None

        return HabitOutputSchema.model_validate(habit)

    async def delete_habit(self, user_id: uuid.UUID, habit_id: uuid.UUID):
        return await self.repo.delete_habit(habit_id=habit_id, creator_id=user_id)
