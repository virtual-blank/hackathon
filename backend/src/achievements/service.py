import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.achievements.models import RuleTypeEnum
from src.achievements.repository import AchievementsRepository


class AchievementsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AchievementsRepository(session=session)

    # вешаем при отметке привычки
    async def check_streak_achievements(self, user_id: uuid.UUID, streak_days: int):
        allowed_achievements_ids = await self.repo.get_allowed_achievements(
            rule_value=streak_days,
            rule_type=RuleTypeEnum.STREAK,
        )
        if not allowed_achievements_ids:
            return None

        for achievement_id in allowed_achievements_ids:
            new_achievement = await self.repo.set_achievement(user_id=user_id, achievement_id=achievement_id)
            if new_achievement:
                # логировать
                print(f"выдана новая ачивка {achievement_id} для user_id: {user_id}")

    # вешаем при отправке/принятии дружбы
    async def check_total_friends_achievements(self, user_id: uuid.UUID):
        total_friends = await self.repo.get_friends_count(user_id=user_id)
        if not total_friends:
            return None

        allowed_achievements_ids = await self.repo.get_allowed_achievements(
            rule_value=total_friends, rule_type=RuleTypeEnum.FRIENDS_COUNT
        )

        if not allowed_achievements_ids:
            return None

        for achievement_id in allowed_achievements_ids:
            new_achievement = await self.repo.set_achievement(user_id=user_id, achievement_id=achievement_id)
            if new_achievement:
                print(f"выдана новая ачивка {achievement_id} для user_id: {user_id}")

    # вешаем при создании привычки
    async def check_total_habits_count_achievements(self, user_id: uuid.UUID):
        total_habits = await self.repo.get_habits_count(user_id=user_id)
        if not total_habits:
            return None

        allowed_achievements_ids = await self.repo.get_allowed_achievements(
            rule_value=total_habits, rule_type=RuleTypeEnum.TOTAL_HABITS
        )

        if not allowed_achievements_ids:
            return None

        for achievement_id in allowed_achievements_ids:
            new_achievement = await self.repo.set_achievement(user_id=user_id, achievement_id=achievement_id)
            if new_achievement:
                print(f"выдана новая ачивка {achievement_id} для user_id: {user_id}")
