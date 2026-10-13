"""
Refresh materialized views по расписанию.

Запуск: python -m src.analytics.workers.scheduler
НЕ запускать в FastAPI-воркерах — иначе refresh будет дублироваться N раз.
"""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from database.db import engine

logger = logging.getLogger(__name__)

HOURLY_VIEWS = ["mv_habit_dashboard", "mv_habit_streaks"]
DAILY_VIEWS = ["mv_habit_daily"]


async def refresh(name: str) -> None:
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {name}")
            )
        logger.info("Refreshed %s", name)
    except Exception:
        logger.exception("Refresh failed: %s", name)


async def main() -> None:
    sched = AsyncIOScheduler(timezone="UTC")

    for name in HOURLY_VIEWS:
        sched.add_job(
            refresh,
            CronTrigger(minute=5),
            args=[name],
            id=name,
            max_instances=1,
            coalesce=True,
        )
    for name in DAILY_VIEWS:
        sched.add_job(
            refresh,
            CronTrigger(hour=3, minute=0),
            args=[name],
            id=name,
            max_instances=1,
            coalesce=True,
        )

    sched.start()
    logger.info("Analytics scheduler started")

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
