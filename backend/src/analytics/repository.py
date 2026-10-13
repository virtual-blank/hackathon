import uuid
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard_rows(self, user_id: uuid.UUID) -> list[dict[str, Any]]:
        """
        Все привычки юзера (созданные + партнёрские) с агрегатами
        из mv_habit_dashboard и mv_habit_streaks.
        """
        result = await self.session.execute(
            text("""
                SELECT
                    d.habit_id,
                    d.title,
                    d.color_hex,
                    d.start_date,
                    d.is_shared,
                    (CURRENT_DATE - d.start_date) AS age_days,
                    d.completion_rate,
                    d.total_completions,
                    COALESCE(s.current_streak, 0) AS current_streak,
                    COALESCE(s.best_streak, 0)    AS best_streak,
                    d.completions_7d,
                    d.completions_prev_7d,
                    d.completions_30d,
                    d.completions_prev_30d,
                    d.last_completed_date,
                    (
                        d.last_completed_date IS NULL
                        OR d.last_completed_date < CURRENT_DATE - 14
                    ) AS is_stale
                FROM mv_habit_dashboard d
                LEFT JOIN mv_habit_streaks s
                    ON s.habit_id = d.habit_id
                   AND s.user_id = d.user_id
                WHERE d.user_id = :uid
                ORDER BY d.title
            """),
            {"uid": user_id},
        )
        return [dict(r) for r in result.mappings().all()]

    async def get_heatmap(
        self,
        user_id: uuid.UUID,
        habit_id: uuid.UUID | None,
        year: int,
    ) -> list[dict[str, Any]]:
        """
        История из mv_habit_daily + «живые» отметки за последние 2 дня
        (чтобы юзер видел свои сегодняшние действия без ожидания refresh).
        """
        start = date(year, 1, 1)
        end = date(year, 12, 31)

        hist = await self.session.execute(
            text("""
                SELECT completed_date AS date, value
                FROM mv_habit_daily
                WHERE user_id = :uid
                  AND (CAST(:hid AS uuid) IS NULL OR habit_id = CAST(:hid AS uuid))
                  AND completed_date BETWEEN :start AND :end
                  AND completed_date < CURRENT_DATE - 1
                ORDER BY completed_date
            """),
            {"uid": user_id, "hid": habit_id, "start": start, "end": end},
        )

        fresh = await self.session.execute(
            text("""
                SELECT completed_date AS date, COUNT(*) AS value
                FROM habit_logs
                WHERE user_id = :uid
                  AND (CAST(:hid AS uuid) IS NULL OR habit_id = CAST(:hid AS uuid))
                  AND completed_date >= CURRENT_DATE - 1
                  AND completed_date BETWEEN :start AND :end
                GROUP BY completed_date
                ORDER BY completed_date
            """),
            {"uid": user_id, "hid": habit_id, "start": start, "end": end},
        )

        merged: dict[date, int] = {r["date"]: r["value"] for r in hist.mappings()}
        for r in fresh.mappings():
            merged[r["date"]] = r["value"]
        return [{"date": d, "value": v} for d, v in sorted(merged.items())]

    async def user_can_access_habit(
        self, user_id: uuid.UUID, habit_id: uuid.UUID
    ) -> bool:
        """Юзер — создатель привычки или принятый партнёр."""
        result = await self.session.execute(
            text("""
                SELECT 1
                FROM habits h
                WHERE h.id = CAST(:hid AS uuid) AND h.creator_id = :uid
                UNION ALL
                SELECT 1
                FROM shared_habit_users shu
                WHERE shu.habit_id = :hid
                  AND shu.user_id = :uid
                  AND shu.status = 'accepted'
                LIMIT 1
            """),
            {"uid": user_id, "hid": habit_id},
        )
        return result.scalar() is not None
