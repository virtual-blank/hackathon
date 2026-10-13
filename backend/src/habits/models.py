import uuid
from datetime import date, time, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Date, ARRAY, Time, text, DateTime, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from database.enum import str_enum
from database.mixins import Uuid7PkMixin, TimeStampMixin
from src.habits.enums import Visibility, InviteStatus

if TYPE_CHECKING:
    from src.users.models import User
    # from src.feed.models import Review


class Habit(Uuid7PkMixin, TimeStampMixin, Base):
    __tablename__ = "habits"

    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(100))

    # формат проверяет Pydantic
    color_hex: Mapped[str] = mapped_column(String(7), default="#4F46E5", server_default="#4F46E5")

    # По умолчанию FRIENDS: так не-друзья ничего не видят.
    visibility: Mapped[Visibility] = mapped_column(
        str_enum(Visibility), default=Visibility.FRIENDS, server_default=Visibility.FRIENDS.value)

    # Первый день отсчёта: сегодня в часовом поясе создателя. Без default, ставит сервис.
    start_date: Mapped[date] = mapped_column(Date)

    # До 3 напоминаний, время в часовом поясе пользователя.
    notification_times: Mapped[list[time]] = mapped_column(
        ARRAY(Time), default=list, server_default=text("'{}'"))

    # Когда ушло последнее напоминание. По одному этому полю определяем, какие из слотов
    # за сегодня уже отправлены (слот отправлен, если last_reminded_at >= время слота).
    # В v1 напоминания получает только создатель.
    last_reminded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creator: Mapped["User"] = relationship(back_populates="habits")
    logs: Mapped[list["HabitLog"]] = relationship(back_populates="habit")
    shared_habit_user: Mapped["SharedHabitUser"] = relationship(back_populates="habit")

    __table_args__ = (
        CheckConstraint("cardinality(notification_times) <= 3", name="max_3_reminders"),
    )


class SharedHabitUser(Uuid7PkMixin, TimeStampMixin, Base):
    """
    Партнёр по совместной привычке. Создатель сюда НЕ пишется, он уже в habits.creator_id.
    Участники = creator_id + user_id (если status = accepted).
    Партнёр отмечает выполнение в habit_logs со своим user_id.
    Совместный стрик = пересечение дат логов создателя и партнёра по этой привычке.
    Отклонить или отменить приглашение = удалить строку.
    Выход партнёра или разрыв дружбы = удалить строку и логи партнёра по этой привычке;
    привычка остаётся у создателя как личная.
    """
    __tablename__ = "shared_habit_users"

    # unique=True: в v1 только пара. Для групп замените на UniqueConstraint("habit_id", "user_id").
    habit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[InviteStatus] = mapped_column(
        str_enum(InviteStatus), default=InviteStatus.PENDING, server_default=InviteStatus.PENDING.value
    )
    # Начало совместного отсчёта (для процентов). Ставит сервис при принятии.
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    habit: Mapped["Habit"] = relationship(back_populates="shared_habit_user")
    user: Mapped["User"] = relationship(back_populates="shared_habit_users")


class HabitLog(Uuid7PkMixin, TimeStampMixin, Base):
    __tablename__ = "habit_logs"

    # Пользователь может отмечать привычку только если:
    # 1. он является создателем привычки;
    # 2. или он принят как партнёр в shared_habit_users.
    # Это бизнес-правило проверяется в service layer.

    habit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # Календарный день в часовом поясе пользователя. БЕЗ default=date.today:
    # это дата сервера, а не пользователя. Дату считает сервис.
    completed_date: Mapped[date] = mapped_column(Date)

    habit: Mapped["Habit"] = relationship(back_populates="logs")
    user: Mapped["User"] = relationship(back_populates="habit_logs")
    # reviews: Mapped[list["Review"]] = relationship(back_populates="habit_log")

    __table_args__ = (
        # Одна отметка в день на человека. Покрывает и запросы «все отметки привычки».
        UniqueConstraint("habit_id", "user_id", "completed_date"),
        # История пользователя по всем привычкам за диапазон дат.
        Index("ix_habit_logs_user_date", "user_id", "completed_date"),
    )
