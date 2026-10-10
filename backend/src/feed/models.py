import uuid
from typing import TYPE_CHECKING

from database.db import Base
from database.mixins import TimeStampMixin, Uuid7PkMixin
from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from src.habits.models import Habit
    from src.users.models import User


class Review(Uuid7PkMixin, TimeStampMixin, Base):
    __tablename__ = "reviews"
    reviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    habit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"))
    comment: Mapped[str | None] = mapped_column(Text)
    rate: Mapped[int]  # 1: пуш, 0: шейм

    habit: Mapped["Habit"] = relationship(back_populates="reviews")

    reviewer: Mapped["User"] = relationship()

    __table_args__ = (
        UniqueConstraint("reviewer_id", "habit_id", name="uq_reviewer_id_habit_log"),
        CheckConstraint("rate IN (0,1)", name="ck_rate"),
    )
