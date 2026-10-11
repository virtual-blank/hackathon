import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.habits.schemas import HabitOutputSchema
from src.users.pfp.minio import DEFAULT_PFP_URL


class ReviewCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    habit_id: uuid.UUID
    comment: str | None = None
    rate: Annotated[int, Field(ge=0, le=1)]


class ReviewUpdateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    habit_id: uuid.UUID
    comment: str | None = None
    rate: Annotated[int, Field(ge=0, le=1)] | None = None


# == Feed Schemas ==
class Reviewer(BaseModel):
    # берется из User
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    pfp_url: str

    @field_validator("pfp_url", mode="before")
    @classmethod
    def set_default_pfp(cls, v: str | None) -> str:
        return v or DEFAULT_PFP_URL


class ReviewOutputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    updated_at: datetime
    habit_id: uuid.UUID
    reviewer: Reviewer
    rate: Annotated[int, Field(ge=0, le=1)]
    comment: str | None = None


class HabitFeedLogOutputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    completed_date: date


class FeedOutputSchema(BaseModel):
    habit: HabitOutputSchema
    total_logs_count: int
    habit_logs: list[HabitFeedLogOutputSchema]  # не забыть в бд: макс 90 записей
    reviews: list[ReviewOutputSchema] = []
