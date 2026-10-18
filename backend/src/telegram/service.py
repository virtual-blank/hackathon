import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_telegram_settings
from src.telegram import client
from src.users.models import User
from src.users.repository import UsersRepository

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UsersRepository(session=session)

    async def generate_link(self, user: User) -> str:

        settings = get_telegram_settings()
        code = secrets.token_urlsafe(32)
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.link_ttl_minutes)

        user.telegram_link_token_hash = code_hash
        user.telegram_link_expires_at = expires_at
        await self.session.commit()

        url = f"https://t.me/{settings.bot_name}?start={code}"
        logger.info("Сгенерирована ссылка привязки для юзера %s", user.id)
        return url

    async def verify_start_code(self, code: str, chat_id: int) -> None:

        code_hash = hashlib.sha256(code.encode()).hexdigest()

        user = await self.repo.get_user_by_telegram_hash(token_hash=code_hash)
        if user is None:
            raise ValueError("Ссылка недействительна")

        if user.telegram_link_expires_at is None or user.telegram_link_expires_at < datetime.now(timezone.utc):
            raise ValueError("Ссылка устарела, сгенерируйте новую")

        existing = await self.repo.get_user_by_telegram_chat_id(chat_id=chat_id)
        if existing is not None and existing.id != user.id:
            raise ValueError("Этот Telegram уже привязан к другому аккаунту")

        user.telegram_chat_id = chat_id
        user.telegram_link_token_hash = None
        user.telegram_link_expires_at = None

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError("Не удалось привязать Telegram, попробуйте позже") from exc

        logger.info("Юзер %s привязал Telegram chat_id=%s", user.id, chat_id)

    async def send_reminder(self, chat_id: int, habit_title: str) -> bool:
        text = f"⏰ Напоминание: привычка «{habit_title}» ещё не выполнена"
        ok = await client.send_message(chat_id=chat_id, text=text)
        if not ok:
            logger.warning(
                "Не удалось отправить напоминание chat_id=%s habit=%s",
                chat_id,
                habit_title,
            )
        return ok
