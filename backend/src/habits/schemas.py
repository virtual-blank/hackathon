import uuid
from datetime import date, datetime, time
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.habits.enums import Visibility


class HabitLogCreateSchema(BaseModel):
    """Схема создания отметки о выполнении привычки."""
    completed_date: date | None = Field(
        default=None,
        description="Календарный день в TZ пользователя. Если None — сервис подставит сегодня.",
    )

    @field_validator("completed_date")
    @classmethod
    def not_in_future(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("Дата не может быть в будущем")
        return v


class HabitCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: Annotated[str, Field(min_length=1, max_length=100)]
    color_hex: Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")] = "#4F46E5"
    visibility: Visibility = Visibility.FRIENDS
    notification_times: Annotated[list[time], Field(
        max_length=3)] = Field(default_factory=list)


class HabitUpdateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: Annotated[str | None, Field(min_length=1, max_length=100)] = None
    color_hex: Annotated[str | None, Field(
        pattern=r"^#[0-9A-Fa-f]{6}$")] = None
    visibility: Visibility | None = None
    notification_times: Annotated[list[time]
                                  | None, Field(max_length=3)] = None


class HabitOutputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    color_hex: str
    visibility: Visibility
    start_date: date
    notification_times: list[time]
    # добавил из TimeStampMixin
    created_at: datetime
    updated_at: datetime


# добавил Даня, мне нужно было для src/feed/schemas
class HabitLogOutputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    habit_id: uuid.UUID
    user_id: uuid.UUID
    completed_date: date
