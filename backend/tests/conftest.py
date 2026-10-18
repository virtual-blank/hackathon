import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_NAME", "test_db")

os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("JWT_SECRET_KEY", "super-secret-test-key-at-least-32-bytes")
os.environ.setdefault("JWT_ALGORITHM", "HS256")

os.environ.setdefault("MINIO_HOST", "localhost")
os.environ.setdefault("MINIO_PORT", "9000")
os.environ.setdefault("MINIO_ROOT_USER", "minio")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "minio123")
os.environ.setdefault("MINIO_BUCKET_NAME", "test-bucket")

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF")
os.environ.setdefault("TELEGRAM_BOT_NAME", "test_bot")

from main import app  
from database.db import get_db  
from src.auth.deps import get_current_user, get_current_user_id  
from src.users.enums import Theme  
from src.users.models import User  


@pytest.fixture
def mock_user() -> User:
    return User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash="hashed_secret",
        theme=Theme.SYSTEM,
        timezone="UTC",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        achievements=[],
    )


@pytest.fixture
def mock_db_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
async def client(mock_db_session: AsyncMock):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(mock_db_session: AsyncMock, mock_user: User):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_user_id] = lambda: mock_user.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()