"""create analytics materialized views

Revision ID: 85b0505cdce3
Revises: 145288589b37
Create Date: 2026-10-13 10:04:51.365583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '85b0505cdce3'
down_revision: Union[str, Sequence[str], None] = '145288589b37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #  mv_habit_dashboard
    op.execute("""
        CREATE MATERIALIZED VIEW mv_habit_dashboard AS
        WITH relevant AS (
            SELECT
                h.id         AS habit_id,
                h.creator_id AS user_id,
                h.title,
                h.color_hex,
                h.start_date,
                FALSE        AS is_shared
            FROM habits h

            UNION ALL

            SELECT
                h.id,
                shu.user_id,
                h.title,
                h.color_hex,
                GREATEST(h.start_date, shu.accepted_at::date) AS start_date,
                TRUE AS is_shared
            FROM habits h
            JOIN shared_habit_users shu ON shu.habit_id = h.id
            WHERE shu.status = 'accepted'
              AND shu.accepted_at IS NOT NULL
        )
        SELECT
            r.habit_id,
            r.user_id,
            r.title,
            r.color_hex,
            r.start_date,
            r.is_shared,
            COUNT(hl.id)                            AS total_completions,
            MAX(hl.completed_date)                  AS last_completed_date,
            COUNT(hl.id) FILTER (
                WHERE hl.completed_date >= CURRENT_DATE - 6
            )                                        AS completions_7d,
            COUNT(hl.id) FILTER (
                WHERE hl.completed_date >= CURRENT_DATE - 13
                  AND hl.completed_date <  CURRENT_DATE - 6
            )                                        AS completions_prev_7d,
            COUNT(hl.id) FILTER (
                WHERE hl.completed_date >= CURRENT_DATE - 29
            )                                        AS completions_30d,
            COUNT(hl.id) FILTER (
                WHERE hl.completed_date >= CURRENT_DATE - 59
                  AND hl.completed_date <  CURRENT_DATE - 29
            )                                        AS completions_prev_30d,
            CASE
                WHEN (CURRENT_DATE - r.start_date + 1) > 0
                THEN ROUND(
                    100.0 * COUNT(hl.id) / (CURRENT_DATE - r.start_date + 1),
                    1
                )
                ELSE 0
            END                                      AS completion_rate
        FROM relevant r
        LEFT JOIN habit_logs hl
            ON hl.habit_id = r.habit_id
           AND hl.user_id = r.user_id
           AND hl.completed_date >= r.start_date
        GROUP BY
            r.habit_id, r.user_id, r.title, r.color_hex,
            r.start_date, r.is_shared
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_mv_habit_dashboard
            ON mv_habit_dashboard (habit_id, user_id)
    """)
    op.execute("""
        CREATE INDEX ix_mv_habit_dashboard_user
            ON mv_habit_dashboard (user_id)
    """)

    # mv_habit_streaks
    op.execute("""
        CREATE MATERIALIZED VIEW mv_habit_streaks AS
        WITH grouped AS (
            SELECT
                habit_id,
                user_id,
                completed_date,
                completed_date - (
                    ROW_NUMBER() OVER (
                        PARTITION BY habit_id, user_id
                        ORDER BY completed_date
                    )
                )::int AS grp
            FROM habit_logs
        ),
        streaks AS (
            SELECT
                habit_id, user_id, grp,
                MIN(completed_date) AS start_d,
                MAX(completed_date) AS end_d,
                COUNT(*)            AS len
            FROM grouped
            GROUP BY habit_id, user_id, grp
        )
        SELECT
            s.habit_id,
            s.user_id,
            COALESCE(
                MAX(s.len) FILTER (WHERE s.end_d >= CURRENT_DATE - 1),
                0
            ) AS current_streak,
            MAX(s.len) AS best_streak
        FROM streaks s
        GROUP BY s.habit_id, s.user_id
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_mv_habit_streaks
            ON mv_habit_streaks (habit_id, user_id)
    """)

    # mv_habit_daily
    op.execute("""
        CREATE MATERIALIZED VIEW mv_habit_daily AS
        SELECT
            habit_id,
            user_id,
            completed_date,
            COUNT(*) AS value
        FROM habit_logs
        GROUP BY habit_id, user_id, completed_date
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_mv_habit_daily
            ON mv_habit_daily (habit_id, user_id, completed_date)
    """)
    op.execute("""
        CREATE INDEX ix_mv_habit_daily_user
            ON mv_habit_daily (user_id, completed_date)
    """)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_habit_daily")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_habit_streaks")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_habit_dashboard")
