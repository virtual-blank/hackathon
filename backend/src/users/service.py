import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.hash_argon import DUMMY_HASH, create_password, verify_password
from src.auth.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from src.users.models import User
from src.users.repository import UsersRepository
from src.users.schemas import AuthOutputSchema, TokenSchema, UserCreateSchema, UserLoginSchema, UserOutputSchema


class UsersService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UsersRepository(session=session)

    async def _issue_tokens(self, user: User) -> AuthOutputSchema:
        """Выдаёт access + refresh, сохраняет refresh в БД."""
        access_str = create_access_token(user_id=user.id)

        refresh_str = create_refresh_token()
        refresh_hash = hash_refresh_token(refresh_str)
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        await self.repo.create_refresh_token(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
        )

        return AuthOutputSchema(
            user=UserOutputSchema.model_validate(user),
            token=TokenSchema(access_token=access_str, refresh_token=refresh_str),
        )

    async def sign_up(self, user_data: UserCreateSchema):
        password = user_data.password.get_secret_value()
        password_hash = await create_password(password=password)
        try:
            new_user_dao = await self.repo.create_user(
                username=user_data.username,
                password_hash=password_hash,
                email=user_data.email,
            )
        except IntegrityError as e:
            if "username" in str(e.orig):
                raise ValueError("Этот юзернейм занят")
            if "email" in str(e.orig):
                raise ValueError("Этот email уже зарегистрирован")
            raise

        return await self._issue_tokens(new_user_dao)

    async def login(self, user_data: UserLoginSchema):
        password = user_data.password.get_secret_value()
        user_dao = await self.repo.get_user_by_username(username=user_data.username)
        if not user_dao:
            await verify_password(password=password, hashed_password=DUMMY_HASH)
            raise ValueError("Неверный логин или пароль")
        is_password_correct = await verify_password(
            password=password, hashed_password=user_dao.password_hash
        )
        if not is_password_correct:
            raise ValueError("Неверный логин или пароль")

        return await self._issue_tokens(user_dao)

    async def refresh(self, refresh_token_str: str) -> AuthOutputSchema:
        """Обновляет access по refresh. Ротирует refresh."""
        token_hash = hash_refresh_token(refresh_token_str)
        token_dao = await self.repo.get_refresh_token_by_hash(token_hash=token_hash)

        if not token_dao:
            raise ValueError("Невалидный refresh-токен")

        if token_dao.revoked_at is not None:
            # Тревога: использован уже отозванный refresh → возможна кража
            await self.repo.revoke_all_user_refresh_tokens(user_id=token_dao.user_id)
            raise ValueError("Refresh-токен отозван")

        if token_dao.expires_at < datetime.now(timezone.utc):
            raise ValueError("Refresh-токен истёк")

        user_dao = await self.repo.get_user_by_id(user_id=token_dao.user_id)
        if not user_dao:
            raise ValueError("Пользователь не найден")

        # Ротация: старый отзываем, выдаём новую пару
        await self.repo.revoke_refresh_token(token_id=token_dao.id)
        return await self._issue_tokens(user_dao)

    async def logout(self, user_id: uuid.UUID) -> None:
        """Отзывает все refresh юзера. Access умрёт сам через exp."""
        await self.repo.revoke_all_user_refresh_tokens(user_id=user_id)

    async def delete_account(self, user_id: uuid.UUID) -> None:
        deleted = await self.repo.delete_user(user_id=user_id)
        if not deleted:
            raise ValueError("Пользователь не найден")