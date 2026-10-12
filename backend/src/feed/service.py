import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from src.feed.repository import FeedRepository
from src.feed.schemas import (
    FeedOutputSchema,
    HabitFeedLogOutputSchema,
    ReviewCreateSchema,
    ReviewOutputSchema,
    ReviewUpdateSchema,
)
from src.habits.schemas import HabitOutputSchema


class FeedService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FeedRepository(session=session)

    async def get_feed(self, user_id: uuid.UUID, limit: int, offset: int):
        feed_dao = await self.repo.get_friends_feed(user_id=user_id, offset=offset, limit=limit)

        result_feed = []

        for habit, total_logs_count in feed_dao:
            result_feed.append(
                FeedOutputSchema(
                    habit=HabitOutputSchema.model_validate(habit),
                    habit_logs=[HabitFeedLogOutputSchema.model_validate(log) for log in habit.logs],
                    reviews=[ReviewOutputSchema.model_validate(review) for review in habit.reviews],
                    total_logs_count=total_logs_count,
                )
            )

        return result_feed

    async def create_review(self, user_id: uuid.UUID, review_dto: ReviewCreateSchema):
        new_review_dao = await self.repo.create_review_and_get_reviewer(
            reviewer_id=user_id, habit_id=review_dto.habit_id, comment=review_dto.comment, rate=review_dto.rate
        )
        if not new_review_dao:
            raise ValueError("Не удалось добавить оценку")
        return ReviewOutputSchema.model_validate(new_review_dao)

    async def edit_review(self, user_id: uuid.UUID, review_id: uuid.UUID, review_update_dto: ReviewUpdateSchema):
        new_review_dict = review_update_dto.model_dump(exclude_unset=True)
        habit_id = new_review_dict.pop("habit_id")

        edited_review_dao = await self.repo.edit_review(
            review_id=review_id, reviewer_id=user_id, habit_id=habit_id, new_review_dict=new_review_dict
        )
        if not edited_review_dao:
            raise ValueError("Не удалось изменить оценку")

    async def delete_review(self, review_id: uuid.UUID, user_id: uuid.UUID):
        is_deleted = await self.repo.delete_review(reviewer_id=user_id, review_id=review_id)
        if not is_deleted:
            raise ValueError("Не удалось удалить оценку")
        return True
