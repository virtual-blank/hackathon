from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from core.config import get_telegram_settings
from core.logger import logging_config, setup_logging
from src.telegram import client as tg_client
from src.notifications.scheduler import start_scheduler, stop_scheduler

# == MODELS ==
from src.users.models import User, UserAchievement
from src.habits.models import Habit, HabitLog, SharedHabitUser
from src.social.models import UserRelation, Message
from src.feed.models import Review
from src.achievements.models import Achievement
# == MODELS ==

# == ROUTERS ==
from src.users.router import router as users_router
from src.feed.router import router as feed_router
from src.users.pfp.router import router as users_pfp_router
from src.habits.router import router as habits_router
from src.social.router import router as social_router
from src.friends.router import router as friends_router
from src.telegram.router import router as telegram_router
from src.social.ws import router as social_ws_router
from src.analytics.router import router as analytics_router
from src.exports.router import router as exports_router
# == ROUTERS ==

# На уровне модуля, а не в lifespan: `fastapi dev` и `uvicorn --reload`
# импортируют main.py в процессе-воркере, и настройка должна случиться там.
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_telegram_settings()
    if settings.webhook_url:
        await tg_client.set_webhook(settings.webhook_url)

    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


ROUTERS_PREFIX = "/api/v1"

app = FastAPI(
    title="Hackathon API",
    version="1.1.0",
    description="API для приложения трекинга привычек",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix=ROUTERS_PREFIX)
app.include_router(feed_router, prefix=ROUTERS_PREFIX)
app.include_router(users_pfp_router, prefix=ROUTERS_PREFIX)
app.include_router(habits_router, prefix=ROUTERS_PREFIX)
app.include_router(social_router, prefix=ROUTERS_PREFIX)
app.include_router(friends_router, prefix=ROUTERS_PREFIX)
app.include_router(telegram_router, prefix=ROUTERS_PREFIX)
app.include_router(social_ws_router, prefix=ROUTERS_PREFIX)
app.include_router(analytics_router, prefix=ROUTERS_PREFIX)
app.include_router(exports_router, prefix=ROUTERS_PREFIX)


@app.get("/health", tags=["🩺 System"], description="Healthcheck")
async def health() -> dict[str, str]:
    """Проверка что сервер запустился йоу"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True, log_config=logging_config())
