from functools import lru_cache

from redis.asyncio import Redis

from core.config import get_redis_settings


@lru_cache
def get_redis() -> Redis:
    """Клиент Redis. Один на процесс: соединения внутри пула переиспользуются."""
    settings = get_redis_settings()
    return Redis.from_url(settings.url, decode_responses=True)
