import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.repository import AnalyticsRepository
from src.analytics.schemas import (
    DashboardResponseSchema,
    DashboardTotalsSchema,
    HabitCardSchema,
    HeatmapDaySchema,
    HeatmapResponseSchema,
    TrendInfo,
)


class AnalyticsError(Exception):
    """Базовое доменное исключение аналитики."""


class HabitNotFoundError(AnalyticsError):
    def __init__(self, habit_id: uuid.UUID):
        self.habit_id = habit_id
        super().__init__(f"Привычка {habit_id} не найдена или недоступна")


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.repo = AnalyticsRepository(session)

    async def get_dashboard(self, user_id: uuid.UUID) -> DashboardResponseSchema:
        rows = await self.repo.get_dashboard_rows(user_id)

        habits: list[HabitCardSchema] = []
        stale: list[HabitCardSchema] = []

        for r in rows:
            card = self._build_card(r)
            (stale if card.is_stale else habits).append(card)

        all_cards = habits + stale
        totals = DashboardTotalsSchema(
            habits_count=len(all_cards),
            active_count=len(habits),
            stale_count=len(stale),
            avg_completion_rate=(
                round(sum(c.completion_rate for c in all_cards) / len(all_cards), 1)
                if all_cards else 0.0
            ),
        )
        return DashboardResponseSchema(habits=habits, stale_habits=stale, totals=totals)

    async def get_heatmap(
        self,
        user_id: uuid.UUID,
        habit_id: uuid.UUID | None,
        year: int,
    ) -> HeatmapResponseSchema:
        if habit_id is not None:
            if not await self.repo.user_can_access_habit(user_id, habit_id):
                raise HabitNotFoundError(habit_id)

        rows = await self.repo.get_heatmap(user_id, habit_id, year)
        return HeatmapResponseSchema(
            habit_id=habit_id,
            year=year,
            days=[HeatmapDaySchema(date=r["date"], value=r["value"]) for r in rows],
        )

    # ---------- helpers ----------

    def _build_card(self, r: dict) -> HabitCardSchema:
        return HabitCardSchema(
            habit_id=r["habit_id"],
            title=r["title"],
            color_hex=r["color_hex"],
            started_at=r["start_date"],
            age_days=r["age_days"],
            completion_rate=r["completion_rate"] or 0.0,
            total_completions=r["total_completions"],
            current_streak=r["current_streak"],
            best_streak=r["best_streak"],
            trend_7d=self._make_trend(
                curr=r["completions_7d"],
                prev=r["completions_prev_7d"],
                period_days=7,
            ),
            trend_30d=self._make_trend(
                curr=r["completions_30d"],
                prev=r["completions_prev_30d"],
                period_days=30,
            ),
            last_completed_date=r["last_completed_date"],
            is_stale=r["is_stale"],
            is_shared=r["is_shared"],
        )

    @staticmethod
    def _make_trend(curr: int, prev: int, period_days: int) -> TrendInfo:
        """
        Тренд в процентных пунктах:
        (curr / period_days) - (prev / period_days), умноженное на 100.
        """
        curr_rate = 100.0 * curr / period_days
        prev_rate = 100.0 * prev / period_days
        delta = round(curr_rate - prev_rate, 1)

        if delta > 1:
            direction = "up"
        elif delta < -1:
            direction = "down"
        else:
            direction = "flat"
        return TrendInfo(delta_pp=delta, direction=direction)
