from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# == MODELS ==
from src.users.models import User, UserAchievement
from src.habits.models import Habit, HabitLog, SharedHabitUser
from src.social.models import UserRelation, Message
from src.feed.models import Review
# == MODELS ==

# == ROUTERS ==
from src.users.router import router as users_router
from src.feed.router import router as feed_router
from src.users.pfp.router import router as users_pfp_router
from src.habits.router import router as habits_router
from src.social.router import router as social_router
# == ROUTERS ==

ROUTERS_PREFIX = "/api/v1"

app = FastAPI(
    title="Hackathon API",
    version="0.1.0",
    description="API для приложения трекинга привычек",
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
app.include_router(feed_router, prefix=ROUTERS_PREFIX)
app.include_router(users_pfp_router, prefix=ROUTERS_PREFIX)
app.include_router(habits_router, prefix=ROUTERS_PREFIX)
app.include_router(social_router, prefix=ROUTERS_PREFIX)


@app.get("/health", tags=["🩺 System"], description="Healthcheck")
async def health() -> dict[str, str]:
    """Проверка что сервер запустился йоу"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
