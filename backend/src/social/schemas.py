import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageCreateSchema(BaseModel):
    """
    Отправка сообщения. Адресуемся собеседником: чат = пара пользователей,
    отдельной сущности «переписка» нет.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    peer_id: uuid.UUID
    content: str = Field(min_length=1, max_length=2000)


class MessageOutputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender_id: uuid.UUID
    receiver_id: uuid.UUID
    content: str
    created_at: datetime
    is_read: bool = False
    read_at: datetime | None = None


class ChatPeerSchema(BaseModel):
    """Собеседник в диалоге. Только публичные поля."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str


class ChatOutputSchema(BaseModel):
    """
    Строка списка диалогов. Диалог определяется собеседником,
    последнее сообщение берём из messages.
    """
    peer: ChatPeerSchema
    last_message_id: uuid.UUID | None = None
    last_message_text: str | None = None
    last_message_at: datetime | None = None
    # Считается на лету по is_read, отдельного счётчика в БД нет.
    unread_count: int = 0


class ReadMessageSchema(BaseModel):
    """Отметка прочтения: всё, что пришло от собеседника до этого сообщения включительно."""
    last_read_message_id: uuid.UUID


class WsTicketSchema(BaseModel):
    """Одноразовый короткоживущий пропуск для подключения к вебсокету."""
    ticket: str
    expires_in: int
