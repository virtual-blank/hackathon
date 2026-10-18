import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import async_session_factory
from src.habits.models import Habit, HabitLog
from src.telegram.service import TelegramService
from src.users.models import User

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
WINDOW = timedelta(minutes=30)


def _get_user_tz(timezone_name: str | None) -> ZoneInfo:
    """Возвращает ZoneInfo юзера, с фолбэком на UTC при неизвестной TZ."""
    if not timezone_name:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        logger.warning("Неизвестная таймзона %r, использую UTC", timezone_name)
        return ZoneInfo("UTC")


def _get_due_slot(habit: Habit, tz: ZoneInfo, now_utc: datetime) -> datetime | None:
    """
    Находит самый свежий наступивший слот в пределах окна WINDOW (30 мин),
    который был не раньше создания привычки и по которому ещё не напоминали.
    """
    now_local = now_utc.astimezone(tz)
    due_slots: list[datetime] = []

    for t in habit.notification_times:
        slot_local = datetime.combine(now_local.date(), t, tzinfo=tz)
        if (
            slot_local <= now_local
            and (now_local - slot_local) <= WINDOW
            and slot_local >= habit.created_at
            and (habit.last_reminded_at is None or habit.last_reminded_at < slot_local)
        ):
            due_slots.append(slot_local)

    return max(due_slots) if due_slots else None


async def _is_completed_today(
    session: AsyncSession,
    *,
    habit_id,
    user_id,
    target_date,
) -> bool:
    """Проверяет, отмечена ли привычка выполненной за target_date."""
    stmt = (
        select(HabitLog.id)
        .where(
            HabitLog.habit_id == habit_id,
            HabitLog.user_id == user_id,
            HabitLog.completed_date == target_date,
        )
        .limit(1)
    )
    return (await session.scalar(stmt)) is not None


async def _process_habit(
    session: AsyncSession,
    tg_service: TelegramService,
    habit: Habit,
    user: User,
    now_utc: datetime,
) -> None:
    tz = _get_user_tz(user.timezone)
    due_slot = _get_due_slot(habit, tz, now_utc)
    if due_slot is None:
        return

    if await _is_completed_today(
        session,
        habit_id=habit.id,
        user_id=user.id,
        target_date=due_slot.date(),
    ):
        return

    sent = await tg_service.send_reminder(
        chat_id=user.telegram_chat_id,
        habit_title=habit.title,
    )
    if sent:
        habit.last_reminded_at = now_utc
        logger.info(
            "Напоминание отправлено: user=%s habit=%s slot=%s",
            user.id,
            habit.id,
            due_slot.time(),
        )
    else:
        logger.warning(
            "Напоминание не доставлено: user=%s habit=%s slot=%s",
            user.id,
            habit.id,
            due_slot.time(),
        )


async def check_reminders() -> None:
    now_utc = datetime.now(timezone.utc)
    async with async_session_factory() as session:
        try:
            stmt = (
                select(Habit, User)
                .join(User, User.id == Habit.creator_id)
                .where(
                    User.telegram_chat_id.is_not(None),
                    User.email.not_like("%@seed.test"),
                    func.cardinality(Habit.notification_times) > 0,
                )
            )
            rows = (await session.execute(stmt)).all()
            tg_service = TelegramService(session=session)

            for habit, user in rows:
                try:
                    await _process_habit(session, tg_service, habit, user, now_utc)
                except Exception:
                    logger.exception(
                        "Ошибка обработки привычки habit=%s user=%s",
                        habit.id,
                        user.id,
                    )

            await session.commit()
        except Exception:
            logger.exception("Ошибка в check_reminders")
            await session.rollback()


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(
            check_reminders,
            "interval",
            minutes=1,
            id="check_reminders",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        logger.info("Планировщик напоминаний запущен (interval=1 мин)")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Планировщик напоминаний остановлен")