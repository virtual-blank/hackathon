"""
Одноразовые пропуска для подключения к вебсокету.

Браузерный WebSocket не умеет передавать заголовок авторизации, поэтому клиент
сначала получает пропуск по REST и предъявляет его при подключении.

Пропуска лежат в Redis с автоистечением, а не в памяти процесса: тогда приложение
можно запускать в несколько воркеров — пропуск, выданный одним процессом,
примет любой другой. Одноразовость обеспечивает атомарный GETDEL.
"""
import secrets
import uuid

from database.redis import get_redis

TICKET_TTL_SECONDS = 30
_TICKET_KEY_PREFIX = "ws_ticket:"


def _key(ticket: str) -> str:
    return f"{_TICKET_KEY_PREFIX}{ticket}"


async def create_ticket(user_id: uuid.UUID, ttl: int = TICKET_TTL_SECONDS) -> str:
    """Создаёт пропуск для пользователя. Redis сам удалит его по истечении TTL."""
    ticket = secrets.token_urlsafe(32)
    await get_redis().set(_key(ticket), str(user_id), ex=ttl)
    return ticket


async def consume_ticket(ticket: str) -> uuid.UUID | None:
    """Возвращает id пользователя и сразу удаляет пропуск: он одноразовый."""
    raw_user_id = await get_redis().getdel(_key(ticket))
    if raw_user_id is None:
        return None
    try:
        return uuid.UUID(raw_user_id)
    except ValueError:
        return None
