"""
Одноразовые пропуска для подключения к вебсокету.

Браузерный WebSocket не умеет передавать заголовок авторизации, поэтому клиент
сначала получает короткоживущий пропуск по REST и предъявляет его при подключении.

Храним в памяти процесса: у нас один воркер и нет Redis (см. docs/chat-schema.md).
Если появится второй процесс — понадобится общее хранилище.
"""
import secrets
import time
import uuid

TICKET_TTL_SECONDS = 30

# ticket -> (user_id, момент истечения в monotonic-времени)
_tickets: dict[str, tuple[uuid.UUID, float]] = {}


def _drop_expired() -> None:
    now = time.monotonic()
    expired = [ticket for ticket, (_, expires_at) in _tickets.items() if expires_at <= now]
    for ticket in expired:
        _tickets.pop(ticket, None)


def create_ticket(user_id: uuid.UUID, ttl: int = TICKET_TTL_SECONDS) -> str:
    _drop_expired()
    ticket = secrets.token_urlsafe(32)
    _tickets[ticket] = (user_id, time.monotonic() + ttl)
    return ticket


def consume_ticket(ticket: str) -> uuid.UUID | None:
    """Возвращает user_id и удаляет пропуск: он одноразовый."""
    _drop_expired()
    data = _tickets.pop(ticket, None)
    if data is None:
        return None
    user_id, expires_at = data
    if expires_at <= time.monotonic():
        return None
    return user_id
