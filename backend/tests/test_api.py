import uuid
from datetime import date, datetime, timezone

from httpx import AsyncClient
import pytest

from src.exceptions.user_exceptions import UsernameTakenError
from src.habits.enums import Visibility
from src.habits.schemas import HabitOutputSchema
from src.habits.service import HabitsService
from src.social.service import SocialService
from src.users.models import User
from src.users.schemas import UserOutputSchema
from src.users.service import UsersService


# == системные ручки и авторизация ==

async def test_healthcheck(client: AsyncClient):
    """Проверка работы /health."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_unauthorized_access_blocked(client: AsyncClient):
    """Запрос к защищенной ручке без токена должен возвращать 401."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


# == ручки пользователей ==

async def test_get_me_authorized(
    auth_client: AsyncClient,
    mock_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    """Авторизованный пользователь получает свой профиль."""
    async def fake_get_me(self, user_id: uuid.UUID):
        return UserOutputSchema.model_validate(mock_user)

    monkeypatch.setattr(UsersService, "get_me", fake_get_me)

    response = await auth_client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == mock_user.username
    assert data["email"] == mock_user.email


async def test_signup_username_taken_returns_409(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Если юзернейм занят, ручка регистрации должна вернуть 409 Conflict."""
    async def fake_sign_up(self, user_data):
        raise UsernameTakenError("Этот юзернейм занят")

    monkeypatch.setattr(UsersService, "sign_up", fake_sign_up)

    response = await client.post(
        "/api/v1/users/sign-up",
        json={
            "username": "takenuser",
            "password": "password123",
            "email": "test@example.com",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Этот юзернейм занят"


# == ручки привычек ==

async def test_create_habit_success(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Успешное создание привычки возвращает 201 и данные привычки."""
    now = datetime.now(timezone.utc)
    fake_habit = HabitOutputSchema(
        id=uuid.uuid4(),
        title="Читать 20 минут",
        color_hex="#4F46E5",
        visibility=Visibility.FRIENDS,
        start_date=date.today(),
        notification_times=[],
        current_streak_days=0,
        max_streak_days=0,
        created_at=now,
        updated_at=now,
    )

    async def fake_create_habit(self, habit_data, user_id):
        return fake_habit

    from src.achievements.service import AchievementsService
    async def fake_ach_bt(user_id):
        return None

    monkeypatch.setattr(HabitsService, "create_habit", fake_create_habit)
    monkeypatch.setattr(AchievementsService, "process_achievements_habits_bt", fake_ach_bt)

    response = await auth_client.post(
        "/api/v1/habits",
        json={"title": "Читать 20 минут", "color_hex": "#4F46E5", "visibility": "friends"},
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Читать 20 минут"


async def test_get_habit_not_found(
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    """Если привычка не найдена, возвращается 404."""
    async def fake_get_habit(self, user_id, habit_id):
        return None

    monkeypatch.setattr(HabitsService, "get_habit", fake_get_habit)

    response = await auth_client.get(f"/api/v1/habits/{uuid.uuid4()}")
    assert response.status_code == 404


# == чат ==

async def test_send_message_to_self_returns_400(
    auth_client: AsyncClient,
    mock_user: User,
):
    """Отправка сообщения самому себе должна возвращать 400 Bad Request."""
    response = await auth_client.post(
        "/api/v1/social/messages",
        json={"receiver_id": str(mock_user.id), "content": "Привет себе!"},
    )
    assert response.status_code == 400
    assert "самому себе" in response.json()["detail"]