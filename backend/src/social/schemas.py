import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════
# HTTP-схемы (для ручек /api/v1/social/messages)
# ═══════════════════════════════════════════════════════════════


class MessageCreateSchema(BaseModel):
    """Отправка сообщения через HTTP (альтернатива WebSocket, удобно для тестов через Swagger)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    receiver_id: uuid.UUID
    content: Annotated[str, Field(min_length=1, max_length=2000)]


class MessageOutputSchema(BaseModel):
    """Сообщение в ответе API."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender_id: uuid.UUID
    receiver_id: uuid.UUID
    content: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime


# ═══════════════════════════════════════════════════════════════
# WebSocket-схемы: клиент → сервер (входящие события)
# ═══════════════════════════════════════════════════════════════


class WSMessageIn(BaseModel):
    """Клиент → сервер: отправить сообщение получателю."""
    model_config = ConfigDict(str_strip_whitespace=True)

    type: Literal["message"]
    receiver_id: uuid.UUID
    content: Annotated[str, Field(min_length=1, max_length=2000)]


class WSHistoryIn(BaseModel):
    """Клиент → сервер: запросить историю переписки с пользователем."""
    model_config = ConfigDict(str_strip_whitespace=True)

    type: Literal["history"]
    peer_id: uuid.UUID
    limit: Annotated[int, Field(ge=1, le=200)] = 50
    # курсорная пагинация: получить сообщения «до» указанного id
    # (UUIDv7 растёт со временем — сортировка по id = сортировка по времени)
    before_id: uuid.UUID | None = None


class WSMarkReadIn(BaseModel):
    """Клиент → сервер: пометить сообщения прочитанными."""
    model_config = ConfigDict(str_strip_whitespace=True)

    type: Literal["mark_read"]
    message_ids: Annotated[list[uuid.UUID], Field(min_length=1)]


# ═══════════════════════════════════════════════════════════════
# WebSocket-схемы: сервер → клиент (исходящие события)
# ═══════════════════════════════════════════════════════════════


class WSNewMessageOut(BaseModel):
    """Сервер → клиент: пришло новое сообщение."""
    type: Literal["new_message"] = "new_message"

    message: MessageOutputSchema


class WSHistoryOut(BaseModel):
    """Сервер → клиент: история сообщений с собеседником."""
    type: Literal["history"] = "history"

    peer_id: uuid.UUID
    messages: list[MessageOutputSchema]


class WSReadOut(BaseModel):
    """Сервер → клиент: собеседник прочитал твои сообщения."""
    type: Literal["read"] = "read"

    by: uuid.UUID  # id того, кто прочитал
    message_ids: list[uuid.UUID]


class WSErrorOut(BaseModel):
    """Сервер → клиент: ошибка обработки события."""
    type: Literal["error"] = "error"

    detail: str


# ═══════════════════════════════════════════════════════════════
# HTTP-схемы: список диалогов, отметка прочтения, пропуск для сокета
# ═══════════════════════════════════════════════════════════════


class MarkReadSchema(BaseModel):
    """Отметка прочтения списком сообщений (для HTTP-ручки)."""
    message_ids: Annotated[list[uuid.UUID], Field(min_length=1)]


class ChatPeerSchema(BaseModel):
    """Собеседник в списке диалогов. Только публичные поля."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str


class ChatOutputSchema(BaseModel):
    """Строка списка диалогов: собеседник, последнее сообщение и непрочитанные."""
    peer: ChatPeerSchema
    last_message_id: uuid.UUID | None = None
    last_message_text: str | None = None
    last_message_at: datetime | None = None
    # Считается на лету по is_read, отдельного счётчика в БД нет.
    unread_count: int = 0


class WsTicketSchema(BaseModel):
    """Одноразовый короткоживущий пропуск для подключения к вебсокету."""
    ticket: str
    expires_in: int


