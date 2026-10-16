import logging
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import async_session_factory
from src.habits.models import Habit, HabitLog
from src.telegram.service import TelegramService
from src.users.models import User

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _get_user_tz(timezone_name: str) -> ZoneInfo:
    """Возвращает ZoneInfo юзера, с фолбэком на UTC при неизвестной TZ."""
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        logger.warning("Неизвестная таймзона %r, использую UTC", timezone_name)
        return ZoneInfo("UTC")


async def _is_completed_today(
    session: AsyncSession,
    *,
    habit_id,
    user_id,
    today_user,
) -> bool:
    """Проверяет, отмечена ли привычка выполненной за today_user."""
    stmt = (
        select(HabitLog.id)
        .where(
            HabitLog.habit_id == habit_id,
            HabitLog.user_id == user_id,
            HabitLog.completed_date == today_user,
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _process_habit(session: AsyncSession, habit: Habit, user: User) -> None:
    """
    Обрабатывает одну привычку:
    - проверяет, выполнена ли сегодня;
    - проходит по слотам notification_times;
    - отправляет напоминание, если слот наступил и ещё не отправляли.
    """
    now_utc = datetime.now(timezone.utc)
    tz = _get_user_tz(user.timezone)
    now_user = now_utc.astimezone(tz)
    today_user = now_user.date()

    if await _is_completed_today(
        session, habit_id=habit.id, user_id=user.id, today_user=today_user,
    ):
        return

    for slot in sorted(habit.notification_times):
        slot_dt_user = datetime.combine(today_user, slot, tzinfo=tz)
        slot_dt_utc = slot_dt_user.astimezone(timezone.utc)

        if slot_dt_utc > now_utc:
            continue

        if slot_dt_user.date() != today_user:
            continue

        if habit.last_reminded_at is not None and habit.last_reminded_at >= slot_dt_utc:
            continue

        sent = await TelegramService(session).send_reminder(
            chat_id=user.telegram_chat_id,
            habit_title=habit.title,
        )
        habit.last_reminded_at = now_utc
        if sent:
            logger.info(
                "Напоминание отправлено: user=%s habit=%s slot=%s",
                user.id, habit.id, slot,
            )
        else:
            logger.warning(
                "Напоминание не доставлено: user=%s habit=%s slot=%s",
                user.id, habit.id, slot,
            )
        break


async def check_reminders() -> None:
    async with async_session_factory() as session:
        try:
            stmt = (
                select(Habit, User)
                .join(User, User.id == Habit.creator_id)
                .where(
                    User.telegram_chat_id.is_not(None),
                    Habit.notification_times != [],
                )
            )
            result = await session.execute(stmt)
            rows = result.all()

            for habit, user in rows:
                try:
                    await _process_habit(session, habit, user)
                except Exception:
                    logger.exception(
                        "Ошибка обработки привычки habit=%s user=%s",
                        habit.id, user.id,
                    )

            await session.commit()

        except Exception:
            logger.exception("Ошибка в check_reminders")
            await session.rollback()


def start_scheduler() -> None:
    scheduler.add_job(
        check_reminders,
        "interval",
        minutes=1,
        id="check_reminders",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Планировщик напоминаний запущен (interval=1 мин)")
    

def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Планировщик напоминаний остановлен")