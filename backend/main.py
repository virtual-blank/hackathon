import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from core.storage import STORAGE_ERRORS, create_bucket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# == MODELS ==
from src.users.models import User, UserAchievement
from src.habits.models import Habit, HabitLog, SharedHabitUser
from src.social.models import UserRelation, Message
# == MODELS ==

# == ROUTERS ==
from src.users.router import router as users_router
# == ROUTERS ==

ROUTERS_PREFIX = "/api/v1"

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await create_bucket()
    except (*STORAGE_ERRORS, ValidationError):
        # Хранилище нужно только фото профиля. Если оно не запущено или не настроено в .env,
        # остальное API должно работать — поэтому пишем в лог и стартуем дальше.
        logger.exception("storage: бакет не подготовлен, загрузка фото профиля работать не будет")
    yield


app = FastAPI(
    title="Hackathon API",
    version="0.1.0",
    description="API для приложения трекинга привычек",
    lifespan=lifespan,
)

# CORS — на хакатоне открываем всё, чтобы фронт с любого порта ходил
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix=ROUTERS_PREFIX)


@app.get("/health", tags=["🩺 System"], description="Healthcheck")
async def health() -> dict[str, str]:
    """Проверка, что сервер запустился."""
    return {"status": "ok"}


# TODO: раскомментировать, когда лид починит hash-argon.py → hash_argon.py
# app.include_router(users_router, prefix="/api")
