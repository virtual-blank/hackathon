import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.achievements.models import Achievement, RuleTypeEnum
from src.habits.models import Habit
from src.social.enums import RelationStatus
from src.social.models import UserRelation
from src.users.models import UserAchievement


class AchievementsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _commit(self):
        await self.session.commit()

    async def get_allowed_achievements(self, rule_value: int, rule_type: RuleTypeEnum):
        stmt = select(Achievement.id).where(Achievement.rule_type == rule_type, Achievement.rule_value == rule_value)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def set_achievement(self, user_id: uuid.UUID, achievement_id: uuid.UUID) -> UserAchievement | None:
        new_achievement = UserAchievement(user_id=user_id, achievement_id=achievement_id)
        self.session.add(new_achievement)
        try:
            await self._commit()
            return new_achievement
        except IntegrityError:
            await self.session.rollback()
            return None

    async def get_friends_count(self, user_id: uuid.UUID):
        stmt = select(func.count(UserRelation.id)).where(
            or_(
                and_(UserRelation.user_id == user_id, UserRelation.status == RelationStatus.ACCEPTED),
                and_(UserRelation.target_id == user_id, UserRelation.status == RelationStatus.ACCEPTED),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_habits_count(self, user_id: uuid.UUID):
        stmt = select(func.count(Habit)).where(Habit.creator_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
