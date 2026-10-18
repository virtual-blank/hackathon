import enum
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base
from database.mixins import TimeStampMixin, Uuid7PkMixin

if TYPE_CHECKING:
    pass


class RuleTypeEnum(str, enum.Enum):
    STREAK = "STREAK"
    FRIENDS_COUNT = "FRIENDS_COUNT"
    TOTAL_HABITS = "TOTAL_HABITS"


class Achievement(Uuid7PkMixin, TimeStampMixin, Base):
    __tablename__ = "achievements"

    name: Mapped[str] = mapped_column(String(25), unique=True)  # название
    rule_type: Mapped[str] = mapped_column(String(32), default="STREAK", server_default="STREAK")  # тип условия ачивки
    rule_value: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # количество для выполнения
    color_hex: Mapped[str] = mapped_column(String(7))  # backround glow color
    requirement: Mapped[str] = mapped_column(String(255))  # описание условий выполнения (строгим текстом)
    description: Mapped[str] = mapped_column(String(255))  # описание (для пользователя)
    icon_url: Mapped[str]  # иконка
