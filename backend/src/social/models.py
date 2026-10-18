import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, CheckConstraint, Index, Text, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from database.db import Base
from database.enum import str_enum
from database.mixins import Uuid7PkMixin, TimeStampMixin
from src.social.enums import RelationStatus

if TYPE_CHECKING:
    from src.users.models import User


class UserRelation(Uuid7PkMixin, TimeStampMixin, Base):
    """
    Дружба и блокировки в одной таблице. Строка направленная:
      PENDING  : user_id отправил заявку target_id
      ACCEPTED : дружба
      BLOCKED  : user_id заблокировал target_id

    Допустимые наборы строк для пары (A, B):
      пусто | A->B pending | A->B accepted (или B->A) | A->B blocked | B->A blocked | оба blocked
    Дружба и блокировка одновременно не существуют. Инвариант держит сервис в одной транзакции:
      - block(A, B): удалить все НЕ-blocked строки пары, затем вставить A->B blocked
        (строку B->A blocked, если она есть, НЕ трогать);
      - заявка A->B запрещена, если есть blocked в любую сторону;
      - если B->A pending уже существует, заявка A->B подтверждает дружбу.
    """

    __tablename__ = "user_relations"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[RelationStatus] = mapped_column(str_enum(RelationStatus))
    user: Mapped["User"] = relationship(
        back_populates="sent_relations",
        foreign_keys=[user_id],
    )

    target: Mapped["User"] = relationship(
        back_populates="received_relations",
        foreign_keys=[target_id],
    )

    __table_args__ = (
        UniqueConstraint("user_id", "target_id"),
        CheckConstraint("user_id <> target_id", name="no_self_relation"),
        Index("ix_user_relations_target_status", "target_id", "status"),
    )


class Message(Uuid7PkMixin, TimeStampMixin, Base):
    """
    Только текст. Приглашения на совместные привычки сюда НЕ пишутся:
    они берутся из shared_habit_users со статусом pending.
    UUIDv7 растёт со временем, поэтому id годится для сортировки и курсорной пагинации.
    """

    __tablename__ = "messages"

    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    receiver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)  # длину (до 2000) проверяет Pydantic

    is_read: Mapped[bool] = mapped_column(default=False, server_default=text("false"), index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sender: Mapped["User"] = relationship(
        back_populates="sent_messages",
        foreign_keys=[sender_id],
    )

    receiver: Mapped["User"] = relationship(
        back_populates="received_messages",
        foreign_keys=[receiver_id],
    )

    __table_args__ = (Index("ix_messages_dialog", "sender_id", "receiver_id", "id"),)
