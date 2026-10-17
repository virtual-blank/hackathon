import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class TrendInfo(BaseModel):
    """Изменение метрики по сравнению с предыдущим периодом."""
    delta_pp: float = Field(..., description="Разница в процентных пунктах")
    direction: str = Field(..., description="up | down | flat")


class HabitCardSchema(BaseModel):
    """Карточка одной привычки на дашборде."""
    model_config = ConfigDict(from_attributes=True)

    habit_id: uuid.UUID
    title: str
    color_hex: str

    # возраст привычки
    started_at: date
    age_days: int

    # выполнение
    completion_rate: float
    total_completions: int

    # серии
    current_streak: int
    best_streak: int

    # тренды
    trend_7d: TrendInfo
    trend_30d: TrendInfo

    # состояние
    last_completed_date: date | None = None
    is_stale: bool = False
    is_shared: bool = False


class DashboardTotalsSchema(BaseModel):
    habits_count: int
    active_count: int
    stale_count: int
    avg_completion_rate: float


class DashboardResponseSchema(BaseModel):
    """Полный ответ главного экрана аналитики."""
    habits: list[HabitCardSchema]
    stale_habits: list[HabitCardSchema]
    totals: DashboardTotalsSchema


class HeatmapDaySchema(BaseModel):
    date: date
    value: int


class HeatmapResponseSchema(BaseModel):
    habit_id: uuid.UUID | None
    year: int
    days: list[HeatmapDaySchema]


class WeekdayStat(BaseModel):
    dow: int = Field(..., ge=1, le=7, description="1=Пн ... 7=Вс")
    completed: int
    available: int
    rate: float


class HabitPattern(BaseModel):
    habit_id: uuid.UUID
    type: str = Field(..., description="daily | custom | sparse | learning")
    active_days: list[int]
    label: str
    weekday_stats: list[WeekdayStat]
