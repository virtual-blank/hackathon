import uuid
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlotlyChartSchema(BaseModel):
    data: list[dict[str, Any]]
    layout: dict[str, Any]


class PlotlyDashboardChartsSchema(BaseModel):
    activity_heatmap: PlotlyChartSchema = Field(description="Линейный/площадной график активности по дням")
    habits_completion_bar: PlotlyChartSchema = Field(description="Горизонтальный бар-чарт % выполнения по привычкам")
    weekday_radar: PlotlyChartSchema = Field(description="Активность по дням недели (Пн-Вс)")


class HabitAnalyticsSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    habit_id: uuid.UUID
    title: str
    color_hex: str
    start_date: date
    is_shared: bool = Field(description="Создатель или приглашенный партнер")

    total_days: int = Field(description="Общее количество дней с момента старта привычки")
    completed_count: int = Field(description="Сколько раз привычка была выполнена")
    completion_rate: float = Field(description="Процент выполнения (0.0 - 100.0)")

    current_streak: int = Field(description="Текущее количество дней подряд")
    max_streak: int = Field(description="Рекорд выполнения (лучший стрик этой привычки)")

    last_completed_date: date | None = Field(default=None, description="Дата последнего выполнения")
    days_since_last_log: int = Field(description="Сколько дней прошло с последнего выполнения (или со старта)")
    is_abandoned: bool = Field(description="Заброшена ли привычка (>= 14 дней без отметок)")
    completed_today: bool = Field(description="Выполнена ли сегодня")

    pushes_count: int = Field(default=0, description="Количество пушей (лайков) от друзей")
    shames_count: int = Field(default=0, description="Количество шеймов от друзей")


class DailyActivityPointSchema(BaseModel):
    date: date
    completed_count: int


class WeekdayActivitySchema(BaseModel):
    weekday_num: int = Field(ge=0, le=6, description="0 - Понедельник, 6 - Воскресенье")
    weekday_name: str
    completed_count: int


class DashboardSummarySchema(BaseModel):
    total_habits: int = Field(description="Всего привычек у пользователя")
    active_habits_count: int = Field(description="Активные привычки (не заброшенные)")
    abandoned_habits_count: int = Field(description="Заброшенные привычки (>= 14 дней без логов)")

    completed_today_count: int = Field(description="Выполнено привычек сегодня")
    today_progress_rate: float = Field(description="% выполнения плана на сегодня")

    total_completions_all_time: int = Field(description="Всего выполнений за все время")
    overall_completion_rate: float = Field(description="Средний % выполнения по всем привычкам")

    best_streak_overall: int = Field(description="Абсолютный рекорд стрика среди всех привычек")
    best_active_streak: int = Field(description="Лучший активный стрик прямо сейчас")

    total_pushes_received: int = Field(description="Всего получено пушей от друзей")
    total_shames_received: int = Field(description="Всего получено шеймов от друзей")
    achievements_unlocked: int = Field(description="Количество открытых ачивок")


class DashboardOutputSchema(BaseModel):
    summary: DashboardSummarySchema
    habits: list[HabitAnalyticsSchema]
    abandoned_habits: list[HabitAnalyticsSchema]
    daily_activity: list[DailyActivityPointSchema]
    weekday_activity: list[WeekdayActivitySchema]
    plotly_charts: PlotlyDashboardChartsSchema
