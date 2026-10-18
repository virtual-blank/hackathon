import json
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from src.habits.enums import Visibility

import plotly.graph_objects as go
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.repository import AnalyticsRepository
from src.analytics.schemas import (
    DailyActivityPointSchema,
    DashboardOutputSchema,
    DashboardSummarySchema,
    HabitAnalyticsSchema,
    PlotlyChartSchema,
    PlotlyDashboardChartsSchema,
    WeekdayActivitySchema,
)
from src.habits.service import calc_streaks
from src.users.models import User

ABANDONED_THRESHOLD_DAYS = 14
WEEKDAY_NAMES_RU = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]
WEEKDAY_SHORT_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AnalyticsRepository(session=session)

    async def get_dashboard(
        self,
        user: User,
        activity_days: int = 30,
        visibilities: list[Visibility] | None = None,
    ) -> DashboardOutputSchema:
        try:
            tz = ZoneInfo(user.timezone or "UTC")
        except ZoneInfoNotFoundError:
            tz = ZoneInfo("UTC")

        now_utc = datetime.now(timezone.utc)
        today_local = now_utc.astimezone(tz).date()

        habits_with_shared = await self.repo.get_user_habits_with_shared(
            user_id=user.id,
            visibilities=visibilities,
        )
        habit_ids = [h.id for h, _ in habits_with_shared]

        logs_map = await self.repo.get_user_logs_dates_by_habit(user_id=user.id, habit_ids=habit_ids)
        reviews_map = await self.repo.get_reviews_counts_by_habit(habit_ids=habit_ids)
        achievements_count = await self.repo.get_achievements_count(user_id=user.id)

        habits_analytics: list[HabitAnalyticsSchema] = []
        daily_counts: dict[date, int] = {}
        weekday_counts: dict[int, int] = {i: 0 for i in range(7)}

        total_completions_all_time = 0
        total_pushes = 0
        total_shames = 0

        for habit, is_shared in habits_with_shared:
            habit_dates = logs_map.get(habit.id, [])
            completed_count = len(habit_dates)
            total_completions_all_time += completed_count

            for d in habit_dates:
                daily_counts[d] = daily_counts.get(d, 0) + 1
                weekday_counts[d.weekday()] += 1

            total_days = max(1, (today_local - habit.start_date).days + 1)

            completion_rate = round(min(100.0, (completed_count / total_days) * 100), 1)

            raw_current_streak, calc_best_streak, expires_at = calc_streaks(habit_dates, tz)
            if raw_current_streak and (expires_at is None or expires_at <= now_utc):
                current_streak = 0
            else:
                current_streak = raw_current_streak

            max_streak = max(habit.max_streak_days if habit.creator_id == user.id else 0, calc_best_streak)

            last_completed_date = habit_dates[-1] if habit_dates else None
            completed_today = last_completed_date == today_local

            if last_completed_date is not None:
                days_since_last = max(0, (today_local - last_completed_date).days)
            else:
                days_since_last = max(0, (today_local - habit.start_date).days)

            is_abandoned = days_since_last >= ABANDONED_THRESHOLD_DAYS

            pushes, shames = reviews_map.get(habit.id, (0, 0))
            total_pushes += pushes
            total_shames += shames

            habits_analytics.append(
                HabitAnalyticsSchema(
                    habit_id=habit.id,
                    title=habit.title,
                    color_hex=habit.color_hex,
                    start_date=habit.start_date,
                    is_shared=is_shared,
                    total_days=total_days,
                    completed_count=completed_count,
                    completion_rate=completion_rate,
                    current_streak=current_streak,
                    max_streak=max_streak,
                    last_completed_date=last_completed_date,
                    days_since_last_log=days_since_last,
                    is_abandoned=is_abandoned,
                    completed_today=completed_today,
                    pushes_count=pushes,
                    shames_count=shames,
                )
            )

        abandoned_habits = [h for h in habits_analytics if h.is_abandoned]
        total_habits = len(habits_analytics)
        active_habits_count = total_habits - len(abandoned_habits)
        completed_today_count = sum(1 for h in habits_analytics if h.completed_today)

        today_progress_rate = round((completed_today_count / total_habits) * 100, 1) if total_habits > 0 else 0.0
        overall_completion_rate = (
            round(sum(h.completion_rate for h in habits_analytics) / total_habits, 1) if total_habits > 0 else 0.0
        )
        best_streak_overall = max((h.max_streak for h in habits_analytics), default=0)
        best_active_streak = max((h.current_streak for h in habits_analytics), default=0)

        summary = DashboardSummarySchema(
            total_habits=total_habits,
            active_habits_count=active_habits_count,
            abandoned_habits_count=len(abandoned_habits),
            completed_today_count=completed_today_count,
            today_progress_rate=today_progress_rate,
            total_completions_all_time=total_completions_all_time,
            overall_completion_rate=overall_completion_rate,
            best_streak_overall=best_streak_overall,
            best_active_streak=best_active_streak,
            total_pushes_received=total_pushes,
            total_shames_received=total_shames,
            achievements_unlocked=achievements_count,
        )

        start_timeline = today_local - timedelta(days=activity_days - 1)
        daily_activity = [
            DailyActivityPointSchema(
                date=start_timeline + timedelta(days=i),
                completed_count=daily_counts.get(start_timeline + timedelta(days=i), 0),
            )
            for i in range(activity_days)
        ]

        weekday_activity = [
            WeekdayActivitySchema(
                weekday_num=i,
                weekday_name=WEEKDAY_NAMES_RU[i],
                completed_count=weekday_counts[i],
            )
            for i in range(7)
        ]

        plotly_charts = self._build_plotly_charts(
            habits=habits_analytics,
            daily_activity=daily_activity,
            weekday_activity=weekday_activity,
        )

        return DashboardOutputSchema(
            summary=summary,
            habits=habits_analytics,
            abandoned_habits=abandoned_habits,
            daily_activity=daily_activity,
            weekday_activity=weekday_activity,
            plotly_charts=plotly_charts,
        )

    @staticmethod
    def _fig_to_schema(fig: go.Figure) -> PlotlyChartSchema:
        fig_dict = json.loads(fig.to_json())
        return PlotlyChartSchema(
            data=fig_dict.get("data", []),
            layout=fig_dict.get("layout", {}),
        )

    def _build_plotly_charts(
        self,
        habits: list[HabitAnalyticsSchema],
        daily_activity: list[DailyActivityPointSchema],
        weekday_activity: list[WeekdayActivitySchema],
    ) -> PlotlyDashboardChartsSchema:
        base_layout = dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=30, b=20),
            autosize=True,
        )

        fig_activity = go.Figure(
            data=[
                go.Scatter(
                    x=[pt.date.isoformat() for pt in daily_activity],
                    y=[pt.completed_count for pt in daily_activity],
                    mode="lines+markers",
                    fill="tozeroy",
                    line=dict(color="#4F46E5", width=3, shape="spline"),
                    marker=dict(size=6, color="#4F46E5"),
                    name="Выполнено",
                )
            ],
            layout=go.Layout(
                **base_layout,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(150,150,150,0.15)", dtick=1),
            ),
        )

        fig_bars = go.Figure(
            data=[
                go.Bar(
                    x=[h.completion_rate for h in habits],
                    y=[h.title for h in habits],
                    orientation="h",
                    marker=dict(color=[h.color_hex for h in habits], cornerradius=6),
                    text=[f"{h.completion_rate}%" for h in habits],
                    textposition="auto",
                    name="% выполнения",
                )
            ],
            layout=go.Layout(
                **base_layout,
                xaxis=dict(range=[0, 100], showgrid=True, gridcolor="rgba(150,150,150,0.15)"),
                yaxis=dict(autorange="reversed", showgrid=False),
            ),
        )

        fig_weekday = go.Figure(
            data=[
                go.Bar(
                    x=WEEKDAY_SHORT_RU,
                    y=[w.completed_count for w in weekday_activity],
                    marker=dict(color="#10B981", cornerradius=6),
                    name="По дням недели",
                )
            ],
            layout=go.Layout(
                **base_layout,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(150,150,150,0.15)"),
            ),
        )

        return PlotlyDashboardChartsSchema(
            activity_heatmap=self._fig_to_schema(fig_activity),
            habits_completion_bar=self._fig_to_schema(fig_bars),
            weekday_radar=self._fig_to_schema(fig_weekday),
        )
