import asyncio
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from database.db import async_session_factory
from src.habits.models import Habit, HabitLog
from src.telegram.service import TelegramService
from src.users.models import User

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SEC = 60
WINDOW = timedelta(minutes=30)


def _due_slot(habit: Habit, tz: ZoneInfo, now_utc: datetime) -> datetime | None:
    now_local = now_utc.astimezone(tz)
    due = []
    for t in habit.notification_times:
        slot = datetime.combine(now_local.date(), t, tzinfo=tz)
        if (
            slot <= now_local
            and now_local - slot <= WINDOW
            and slot >= habit.created_at  # слот до создания привычки (не напоминаем)
            and (habit.last_reminded_at is None or habit.last_reminded_at < slot)
        ):
            due.append(slot)
    return max(due) if due else None


async def _tick() -> None:
    now_utc = datetime.now(timezone.utc)
    async with async_session_factory() as session:
        rows = (
            await session.execute(
                select(Habit, User.timezone, User.telegram_chat_id)
                .join(User, User.id == Habit.creator_id)
                .where(
                    User.telegram_chat_id.is_not(None),
                    User.email.not_like("%@seed.test"),
                    func.cardinality(Habit.notification_times) > 0,
                )
            )
        ).all()

        service = TelegramService(session=session)
        for habit, tz_name, chat_id in rows:
            try:
                tz = ZoneInfo(tz_name or "UTC")
            except Exception:
                tz = ZoneInfo("UTC")

            slot = _due_slot(habit, tz, now_utc)
            if slot is None:
                continue

            done = await session.scalar(
                select(HabitLog.id)
                .where(
                    HabitLog.habit_id == habit.id,
                    HabitLog.user_id == habit.creator_id,
                    HabitLog.completed_date == slot.date(),
                )
                .limit(1)
            )
            if done:
                continue

            if await service.send_reminder(chat_id=chat_id, habit_title=habit.title):
                habit.last_reminded_at = now_utc

        await session.commit()


async def reminders_loop() -> None:
    while True:
        try:
            await _tick()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ошибка в цикле напоминаний")
        await asyncio.sleep(CHECK_INTERVAL_SEC)
