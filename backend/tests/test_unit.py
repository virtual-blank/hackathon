import uuid
from datetime import date, timedelta
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from src.auth.hash_argon import create_password, verify_password
from src.auth.security import create_access_token, decode_access_token
from src.exceptions.auth_exceptions import InvalidTokenError
from src.habits.schemas import HabitCreateSchema, HabitLogCreateSchema
from src.habits.service import calc_streaks
from src.users.schemas import UserCreateSchema


# == подсчет стриков ==

def test_calc_streaks_empty():
    """Если дат нет — стрик должен быть 0."""
    current, best, expires = calc_streaks([], ZoneInfo("UTC"))
    assert current == 0
    assert best == 0
    assert expires is None


def test_calc_streaks_consecutive_days():
    """Проверка непрерывного стрика в 3 дня подряд."""
    dates = [date(2026, 10, 10), date(2026, 10, 11), date(2026, 10, 12)]
    current, best, expires = calc_streaks(dates, ZoneInfo("UTC"))
    assert current == 3
    assert best == 3
    assert expires is not None


def test_calc_streaks_with_break():
    """Если был перерыв: лучший стрик сохраняется, а текущий сбрасывается."""
    dates = [
        date(2026, 10, 1),
        date(2026, 10, 2),
        date(2026, 10, 3),  # стрик из 3х дней
        # перерыв
        date(2026, 10, 10),
        date(2026, 10, 11),  # стрик из 2х дней
    ]
    current, best, _ = calc_streaks(dates, ZoneInfo("UTC"))
    assert current == 2
    assert best == 3


# == jwt и пароли ==

def test_jwt_create_and_decode():
    """Созданный токен должен успешно декодироваться в тот же user_id."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id)
    decoded_id = decode_access_token(token)
    assert decoded_id == user_id


def test_jwt_expired_token():
    """Просроченный токен должен вызывать ошибку InvalidTokenError."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, expires_delta=timedelta(seconds=-10))
    with pytest.raises(InvalidTokenError, match="Токен истёк"):
        decode_access_token(token)


async def test_password_hashing():
    """Хеширование пароля Argon2 и его проверка."""
    raw_password = "MyStrongPassword123"
    hashed = await create_password(raw_password)

    assert hashed != raw_password
    assert await verify_password(raw_password, hashed) is True
    assert await verify_password("WrongPassword", hashed) is False


# == валидация pydantic-схем ==

def test_user_create_schema_lowercase():
    """Юзернейм при регистрации должен автоматически переводиться в нижний регистр."""
    schema = UserCreateSchema(
        username="CoolUser_1",
        password="secretpassword",
        email="user@example.com",
    )
    assert schema.username == "cooluser_1"


def test_habit_create_invalid_hex_color():
    """Неправильный HEX-цвет привычки должен вызывать ошибку валидации."""
    with pytest.raises(ValidationError):
        HabitCreateSchema(title="Бег", color_hex="not-a-color")


def test_habit_log_future_date_forbidden():
    """Нельзя отметить выполнение привычки датой из будущего."""
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError, match="Дата не может быть в будущем"):
        HabitLogCreateSchema(completed_date=tomorrow)