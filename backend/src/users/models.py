import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from database.enum import str_enum
from database.mixins import TimeStampMixin, Uuid7PkMixin
from src.users.enums import Theme, TimezoneEnum

if TYPE_CHECKING:
    from src.achievements.models import Achievement
    from src.habits.models import Habit, HabitLog, SharedHabitUser
    from src.social.models import Message, UserRelation


class User(Uuid7PkMixin, TimeStampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(16), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    pfp_url: Mapped[str | None] = mapped_column(default=None)
    # Настройки (вместо отдельной таблицы users_settings)
    theme: Mapped[Theme] = mapped_column(str_enum(Theme), default=Theme.SYSTEM, server_default=Theme.SYSTEM.value)

    # todo: добавить позже:
    # timezone: Mapped[TimezoneEnum] = mapped_column(server_default=TimezoneEnum.UTC)
    timezone: Mapped[str] = mapped_column(String(64), server_default="UTC")

    # Telegram. chat_id у Telegram числовой и может быть больше int32.
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    # Одноразовая ссылка привязки t.me/<bot>?start=<token>. В БД только хеш токена.
    telegram_link_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    telegram_link_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    habits: Mapped[list["Habit"]] = relationship(back_populates="creator")
    habit_logs: Mapped[list["HabitLog"]] = relationship(back_populates="user")
    achievements: Mapped[list["UserAchievement"]] = relationship(back_populates="user")
    shared_habit_users: Mapped[list["SharedHabitUser"]] = relationship(back_populates="user")
    sent_relations: Mapped[list["UserRelation"]] = relationship(
        back_populates="user",
        foreign_keys="UserRelation.user_id",
    )

    received_relations: Mapped[list["UserRelation"]] = relationship(
        back_populates="target",
        foreign_keys="UserRelation.target_id",
    )

    sent_messages: Mapped[list["Message"]] = relationship(
        back_populates="sender",
        foreign_keys="Message.sender_id",
    )

    received_messages: Mapped[list["Message"]] = relationship(
        back_populates="receiver",
        foreign_keys="Message.receiver_id",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserAchievement(Uuid7PkMixin, TimeStampMixin, Base):
    """Достижение уровня пользователя, не привязано к конкретной привычке."""

    __tablename__ = "user_achievements"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    achievement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("achievements.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "user_id", "achievement_id", name="(uq_user_id_achievement_id) "
        ),  # индекс по user_id получается бесплатно
    )


class RefreshToken(Uuid7PkMixin, TimeStampMixin, Base):
    """Refresh-токен. Opaque-строка, хранится в БД, отзывается через logout."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
