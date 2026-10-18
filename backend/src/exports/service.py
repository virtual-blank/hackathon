import csv
import io
import uuid
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.service import AnalyticsService
from src.exports.schemas import ExportDelimiter
from src.habits.models import Habit, HabitLog
from src.users.models import User


class ExportsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analytics_service = AnalyticsService(session=session)

    async def export_habits_summary_csv(
        self,
        user: User,
        delimiter: ExportDelimiter = ExportDelimiter.COMMA,
    ) -> tuple[str, str]:
        dashboard = await self.analytics_service.get_dashboard(user=user, activity_days=30)

        output = io.StringIO()
        output.write("\ufeff")

        writer = csv.writer(output, delimiter=delimiter.value, quoting=csv.QUOTE_MINIMAL)

        # заголовки
        writer.writerow(
            [
                "ID привычки",
                "Название",
                "Цвет (HEX)",
                "Дата начала",
                "Дней с начала",
                "Выполнено раз",
                "Процент выполнения (%)",
                "Текущий стрик (дней)",
                "Рекорд стрика (дней)",
                "Последнее выполнение",
                "Дней без отметок",
                "Заброшена (>=14 дней)",
                "Выполнена сегодня",
                "Пуши (лайки)",
                "Шеймы (дизлайки)",
            ]
        )

        for h in dashboard.habits:
            writer.writerow(
                [
                    str(h.habit_id),
                    h.title,
                    h.color_hex,
                    h.start_date.isoformat(),
                    h.total_days,
                    h.completed_count,
                    h.completion_rate,
                    h.current_streak,
                    h.max_streak,
                    h.last_completed_date.isoformat() if h.last_completed_date else "",
                    h.days_since_last_log,
                    "Да" if h.is_abandoned else "Нет",
                    "Да" if h.completed_today else "Нет",
                    h.pushes_count,
                    h.shames_count,
                ]
            )

        today_str = self._get_user_today(user).isoformat()
        filename = f"habits_summary_{user.username}_{today_str}.csv"
        return output.getvalue(), filename

    async def export_habit_logs_csv(
        self,
        user: User,
        date_from: date | None = None,
        date_to: date | None = None,
        habit_id: uuid.UUID | None = None,
        delimiter: ExportDelimiter = ExportDelimiter.COMMA,
    ) -> tuple[str, str]:
        if date_from and date_to and date_from > date_to:
            raise ValueError("Начальная дата (date_from) не может быть позже конечной (date_to)")

        stmt = (
            select(
                HabitLog.completed_date,
                Habit.id.label("habit_id"),
                Habit.title,
                Habit.visibility,
                HabitLog.created_at,
            )
            .join(Habit, Habit.id == HabitLog.habit_id)
            .where(HabitLog.user_id == user.id)
            .order_by(HabitLog.completed_date.desc(), Habit.title.asc())
        )

        if habit_id is not None:
            stmt = stmt.where(HabitLog.habit_id == habit_id)
        if date_from is not None:
            stmt = stmt.where(HabitLog.completed_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(HabitLog.completed_date <= date_to)

        result = await self.session.execute(stmt)
        rows = result.all()

        output = io.StringIO()
        output.write("\ufeff")

        writer = csv.writer(output, delimiter=delimiter.value, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(
            [
                "Дата выполнения",
                "День недели",
                "ID привычки",
                "Название привычки",
                "Приватность",
                "Время отметки (UTC)",
            ]
        )

        weekday_names = [
            "Понедельник",
            "Вторник",
            "Среда",
            "Четверг",
            "Пятница",
            "Суббота",
            "Воскресенье",
        ]

        for row in rows:
            writer.writerow(
                [
                    row.completed_date.isoformat(),
                    weekday_names[row.completed_date.weekday()],
                    str(row.habit_id),
                    row.title,
                    row.visibility.value if hasattr(row.visibility, "value") else str(row.visibility),
                    row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else "",
                ]
            )

        today_str = self._get_user_today(user).isoformat()
        filename = f"habits_logs_{user.username}_{today_str}.csv"
        return output.getvalue(), filename

    @staticmethod
    def _get_user_today(user: User) -> date:
        try:
            tz = ZoneInfo(user.timezone or "UTC")
        except ZoneInfoNotFoundError:
            tz = ZoneInfo("UTC")
        return datetime.now(timezone.utc).astimezone(tz).date()
