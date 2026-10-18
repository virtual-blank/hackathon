import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.feed.repository import FeedRepository
from src.feed.schemas import (
    FeedOutputSchema,
    HabitFeedLogOutputSchema,
    ReviewCreateSchema,
    Reviewer,
    ReviewOutputSchema,
    ReviewUpdateSchema,
)
from src.habits.schemas import HabitOutputSchema


class FeedService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FeedRepository(session=session)

    async def get_feed(self, user_id: uuid.UUID, limit: int, offset: int) -> list[FeedOutputSchema]:
        feed_dao = await self.repo.get_friends_feed(user_id=user_id, offset=offset, limit=limit)

        result_feed = []
        for habit, total_logs_count in feed_dao:
            result_feed.append(
                FeedOutputSchema(
                    creator=Reviewer.model_validate(habit.creator),
                    habit=HabitOutputSchema.from_habit(habit),
                    habit_logs=[HabitFeedLogOutputSchema.model_validate(log) for log in habit.logs],
                    reviews=[ReviewOutputSchema.model_validate(review) for review in habit.reviews],
                    total_logs_count=total_logs_count,
                )
            )
        return result_feed

    async def create_review(self, user_id: uuid.UUID, review_dto: ReviewCreateSchema) -> ReviewOutputSchema:
        await self.repo.can_user_review_habit(user_id=user_id, habit_id=review_dto.habit_id)

        new_review_dao = await self.repo.create_review_and_get_reviewer(
            reviewer_id=user_id,
            habit_id=review_dto.habit_id,
            comment=review_dto.comment,
            rate=review_dto.rate,
        )
        return ReviewOutputSchema.model_validate(new_review_dao)

    async def edit_review(
        self, user_id: uuid.UUID, review_id: uuid.UUID, review_update_dto: ReviewUpdateSchema
    ) -> ReviewOutputSchema:
        new_review_dict = review_update_dto.model_dump(exclude_unset=True)
        new_review_dict.pop("habit_id", None)

        if "rate" in new_review_dict and new_review_dict["rate"] is None:
            raise ValueError("Оценка не может быть пустой")

        if not new_review_dict:
            raise ValueError("Не указаны поля для обновления")

        edited_review_dao = await self.repo.edit_review(
            review_id=review_id,
            reviewer_id=user_id,
            new_review_dict=new_review_dict,
        )
        if not edited_review_dao:
            raise ValueError("Оценка не найдена или нет прав на её изменение")

        return ReviewOutputSchema.model_validate(edited_review_dao)

    async def delete_review(self, review_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        is_deleted = await self.repo.delete_review(reviewer_id=user_id, review_id=review_id)
        if not is_deleted:
            raise ValueError("Оценка не найдена или нет прав на её удаление")
        return True
