import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.telegram import client
from src.telegram.schemas import TelegramWebhookSchema
from src.telegram.service import TelegramService

logger = logging.getLogger(__name__)


async def handle_update(update_data: dict, session: AsyncSession) -> None:
    try:
        update = TelegramWebhookSchema.model_validate(update_data)
    except Exception as exc:
        logger.warning("Не удалось распарсить апдейт Telegram: %s", exc)
        return

    try:
        message = update.message
        if message is None:
            return
        text = message.text
        if text is None:
            return
        chat_id = message.chat.id
        if text.startswith("/start"):
            await _handle_start(text=text, chat_id=chat_id, session=session)
        else:
            logger.info("Неизвестная команда от chat_id=%s: %s", chat_id, text)
    except Exception:
        logger.exception("ОШИБКА обработки апдейта Telegram")


async def _handle_start(text: str, chat_id: int, session: AsyncSession) -> None:
    parts = text.split(maxsplit=1)

    if len(parts) == 1:
        await client.send_message(
            chat_id=chat_id,
            text=(
                "👋 Привет! Я бот-помощник для трекинга привычек.\n\n"
                "Чтобы привязать аккаунт — перейди по ссылке из веб-приложения "
                "(кнопка «Привязать Telegram»)."
            ),
        )
        return

    code = parts[1].strip()
    if not code:
        await client.send_message(chat_id=chat_id, text="❌ Пустой код привязки")
        return

    service = TelegramService(session=session)
    try:
        await service.verify_start_code(code=code, chat_id=chat_id)
    except ValueError as exc:
        logger.info("Привязка отклонена для chat_id=%s: %s", chat_id, exc)
        await client.send_message(chat_id=chat_id, text=f"❌ {exc}")
        return
    except Exception:
        logger.exception("НЕОЖИДАННАЯ ОШИБКА при привязке chat_id=%s", chat_id)
        await client.send_message(chat_id=chat_id, text="❌ Внутренняя ошибка")
        return

    await client.send_message(
        chat_id=chat_id,
        text="✅ Telegram привязан! Теперь ты будешь получать напоминания о привычках.",
    )
