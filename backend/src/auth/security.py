import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from core.config import get_jwt_settings
from src.exceptions.auth_exceptions import InvalidTokenError

ACCESS_TOKEN_EXPIRE_MINUTES = get_jwt_settings().access_token_expire_minutes
SECRET_KEY = get_jwt_settings().secret_key
ALGORITHM = get_jwt_settings().algorithm
REFRESH_TOKEN_EXPIRE_DAYS = get_jwt_settings().refresh_token_expire_days


def create_access_token(user_id: uuid.UUID, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise InvalidTokenError("Токен истёк") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("Невалидный токен") from exc

    sub = payload.get("sub")
    if sub is None:
        raise InvalidTokenError("Токен без sub")
    try:
        return uuid.UUID(sub)
    except ValueError as exc:
        raise InvalidTokenError("Некорректный sub в токене") from exc


def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
