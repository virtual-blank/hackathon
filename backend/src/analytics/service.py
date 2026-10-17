import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.repository import AnalyticsRepository
from src.analytics.schemas import (
    DashboardResponseSchema,
    DashboardTotalsSchema,
    HabitCardSchema,
    HabitPattern,
    HeatmapDaySchema,
    HeatmapResponseSchema,
    TrendInfo,
    WeekdayStat,
)


class AnalyticsError(Exception):
    """Базовое доменное исключение аналитики."""


class HabitNotFoundError(AnalyticsError):
    def __init__(self, habit_id: uuid.UUID):
        self.habit_id = habit_id
        super().__init__(f"Привычка {habit_id} не найдена или недоступна")


_DOW_NAMES = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"}


def _count_weekdays_between(start: date, end: date, dow: int) -> int:
    """Сколько раз день недели dow встречался между start и end включительно."""
    total_days = (end - start).days + 1
    if total_days <= 0:
        return 0
    full_weeks = total_days // 7
    remainder = total_days % 7
    start_dow = start.isoweekday()
    count = full_weeks
    for i in range(remainder):
        if (start_dow + i - 1) % 7 + 1 == dow:
            count += 1
    return count


def _detect_pattern(weekday_stats: list[dict], age_days: int) -> dict:
    if age_days < 14:
        return {"type": "learning", "active_days": [], "label": "Мало данных"}
    active = [s["dow"] for s in weekday_stats if s["rate"] >= 30 and s["completed"] >= 2]
    if not active:
        return {"type": "sparse", "active_days": [], "label": "Нет паттерна"}
    if len(active) >= 6:
        return {"type": "daily", "active_days": list(range(1, 8)), "label": "Ежедневно"}
    return {
        "type": "custom",
        "active_days": sorted(active),
        "label": ", ".join(_DOW_NAMES[d] for d in sorted(active)),
    }


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
        self, user_id: uuid.UUID, habit_id: uuid.UUID | None, year: int,
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

    async def get_weekday_patterns(self, user_id: uuid.UUID) -> list[HabitPattern]:
        rows = await self.repo.get_weekday_completions(user_id)
        if not rows:
            return []

        by_habit: dict[uuid.UUID, dict[int, int]] = {}
        for r in rows:
            by_habit.setdefault(r["habit_id"], {})[r["dow"]] = r["completed"]

        dashboard_rows = await self.repo.get_dashboard_rows(user_id)
        patterns: list[HabitPattern] = []

        for d in dashboard_rows:
            hid = d["habit_id"]
            if hid not in by_habit:
                continue
            completions = by_habit[hid]
            age_days = d["age_days"]
            start = d["start_date"]
            today = date.today()

            stats: list[WeekdayStat] = []
            for dow in range(1, 8):
                available = _count_weekdays_between(start, today, dow)
                completed = completions.get(dow, 0)
                rate = round(100.0 * completed / available, 1) if available else 0.0
                stats.append(WeekdayStat(
                    dow=dow, completed=completed, available=available, rate=rate,
                ))

            detected = _detect_pattern([s.model_dump() for s in stats], age_days)
            patterns.append(HabitPattern(habit_id=hid, weekday_stats=stats, **detected))

        return patterns

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
                curr=r["completions_7d"], prev=r["completions_prev_7d"], period_days=7,
            ),
            trend_30d=self._make_trend(
                curr=r["completions_30d"], prev=r["completions_prev_30d"], period_days=30,
            ),
            last_completed_date=r["last_completed_date"],
            is_stale=r["is_stale"],
            is_shared=r["is_shared"],
        )

    @staticmethod
    def _make_trend(curr: int, prev: int, period_days: int) -> TrendInfo:
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
