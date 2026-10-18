import logging

import httpx

from core.config import get_telegram_settings

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


def _api_url(method: str) -> str:
    """Собирает URL метода Telegram Bot API."""
    token = get_telegram_settings().bot_token
    return f"{TELEGRAM_API_BASE}/bot{token}/{method}"


async def send_message(chat_id: int, text: str) -> bool:
    """
    Отправляет текстовое сообщение в Telegram.
    Возвращает True, если доставлено, False — иначе.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                _api_url("sendMessage"),
                json={"chat_id": chat_id, "text": text},
            )
            data = response.json()
            if not data.get("ok"):
                logger.warning("Telegram sendMessage не сработал: %s", data)
                return False
            return True
    except httpx.HTTPError as exc:
        logger.error("Telegram sendMessage: ошибка HTTP: %s", exc)
        return False


async def set_webhook(url: str) -> bool:
    """
    Регистрирует webhook в Telegram.
    Вызывается один раз при старте приложения (если url задан).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                _api_url("setWebhook"),
                json={"url": url},
            )
            data = response.json()
            if not data.get("ok"):
                logger.warning("Telegram setWebhook не сработал: %s", data)
                return False
            logger.info("Telegram webhook зарегистрирован: %s", url)
            return True
    except httpx.HTTPError as exc:
        logger.error("Telegram setWebhook: ошибка HTTP: %s", exc)
        return False


async def get_me() -> dict | None:
    """
    Проверка, что токен рабочий. Возвращает данные бота.
    Полезно для отладки.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(_api_url("getMe"))
            data = response.json()
            if not data.get("ok"):
                logger.warning("Telegram getMe не сработал: %s", data)
                return None
            return data.get("result")
    except httpx.HTTPError as exc:
        logger.error("Telegram getMe: ошибка HTTP: %s", exc)
        return None
