import logging

from fastapi import APIRouter, HTTPException, Request, status

from src.auth.deps import CurrentUserDep, SessionDep
from src.telegram.handlers import handle_update
from src.telegram.schemas import TelegramLinkOutputSchema
from src.telegram.service import TelegramService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["📱 Telegram"])


# == GENERATE LINK ==
@router.post(
    "/link",
    status_code=status.HTTP_200_OK,
    response_model=TelegramLinkOutputSchema,
    description="Generate Telegram link",
)
async def generate_telegram_link(user: CurrentUserDep, session: SessionDep):
    """Генерирует одноразовую ссылку для привязки Telegram."""
    service = TelegramService(session=session)
    try:
        url = await service.generate_link(user=user)
    except Exception:
        logger.exception("Не удалось сгенерировать ссылку привязки Telegram user_id=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return TelegramLinkOutputSchema(url=url)


# == WEBHOOK ==
@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    description="Telegram webhook",
)
async def telegram_webhook(request: Request, session: SessionDep):
    """
    Принимает апдейты от Telegram.
    Всегда отвечает 200, чтобы Telegram не ретраил.
    """
    try:
        update_data = await request.json()
    except Exception:
        logger.warning("Webhook получил невалидный JSON")
        return {"ok": True}

    try:
        await handle_update(update_data=update_data, session=session)
    except Exception:
        logger.exception("Ошибка обработки апдейта Telegram")

    return {"ok": True}
