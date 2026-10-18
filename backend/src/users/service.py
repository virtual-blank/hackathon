import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.exceptions.user_exceptions import (
    UsernameTakenError,
    IncorrectPassword,
    AuthError,
    UserNotFoundError,
    DataFormatError,
)

from src.auth.hash_argon import DUMMY_HASH, create_password, verify_password
from src.auth.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from src.users.models import User
from src.users.repository import UsersRepository
from src.users.schemas import (
    AuthOutputSchema,
    TokenSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserOutputSchema,
    UserPasswordUpdateSchema,
    UserUpdateSchema,
    UserSearchSchema,
)


class UsersService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UsersRepository(session=session)

    async def _issue_tokens(self, user: User) -> AuthOutputSchema:
        """Выдаёт access + refresh, сохраняет refresh в БД."""
        access_str = create_access_token(user_id=user.id)

        refresh_str = create_refresh_token()
        refresh_hash = hash_refresh_token(refresh_str)
        expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

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
                raise UsernameTakenError("Этот юзернейм занят")
            if "email" in str(e.orig):
                raise UsernameTakenError("Этот email уже зарегистрирован")
            raise

        return await self._issue_tokens(new_user_dao)

    async def login(self, user_data: UserLoginSchema):
        password = user_data.password.get_secret_value()
        user_dao = await self.repo.get_user_by_username(username=user_data.username)
        if not user_dao:
            await verify_password(password=password, hashed_password=DUMMY_HASH)
            raise IncorrectPassword("Неверный логин или пароль")
        is_password_correct = await verify_password(password=password, hashed_password=user_dao.password_hash)
        if not is_password_correct:
            raise IncorrectPassword("Неверный логин или пароль")

        return await self._issue_tokens(user_dao)

    async def refresh(self, refresh_token_str: str) -> AuthOutputSchema:
        """Обновляет access по refresh. Ротирует refresh."""
        token_hash = hash_refresh_token(refresh_token_str)
        token_dao = await self.repo.get_refresh_token_by_hash(token_hash=token_hash)

        if not token_dao:
            raise AuthError("Невалидный refresh-токен")

        if token_dao.revoked_at is not None:
            if datetime.now(UTC) - token_dao.revoked_at > timedelta(seconds=30):
                await self.repo.revoke_all_user_refresh_tokens(user_id=token_dao.user_id)
            raise AuthError("Refresh-токен отозван")

        if token_dao.expires_at < datetime.now(UTC):
            raise AuthError("Refresh-токен истёк")

        user_dao = await self.repo.get_user_by_id(user_id=token_dao.user_id)
        if not user_dao:
            raise UserNotFoundError("Пользователь не найден")

        await self.repo.revoke_refresh_token(token_id=token_dao.id)
        return await self._issue_tokens(user_dao)

    async def logout(self, user_id: uuid.UUID) -> None:
        """Отзывает все refresh юзера. Access умрёт сам через exp."""
        await self.repo.revoke_all_user_refresh_tokens(user_id=user_id)

    async def delete_account(self, user_id: uuid.UUID) -> None:
        deleted = await self.repo.delete_user(user_id=user_id)
        if not deleted:
            raise UserNotFoundError("Пользователь не найден")

    async def get_me(self, user_id: uuid.UUID):
        user_dao = await self.repo.get_user_by_id(user_id=user_id)
        return UserOutputSchema.model_validate(user_dao)

    async def edit_profile(self, user_id: uuid.UUID, user_data: UserUpdateSchema):
        user_data_dict = user_data.model_dump(exclude_unset=True, exclude_none=True)
        if not user_data_dict:
            raise DataFormatError("Данные не могут быть пустые")
        try:
            updated_user = await self.repo.edit_profile(user_id=user_id, user_data_dict=user_data_dict)
            if not updated_user:
                raise UserNotFoundError("Не удалось внести изменения")
            user = await self.repo.get_user_by_id(user_id=updated_user.id)
            return UserOutputSchema.model_validate(user)

        except IntegrityError as exc:
            exc_text = str(exc.orig)
            await self.repo._rollback()
            if "username" in exc_text:
                raise UsernameTakenError("Этот юзернейм занят")
            if "email" in exc_text:
                raise UsernameTakenError("Этот имейл уже кем-то используется")
            if "timezone" in exc_text:
                raise DataFormatError("Часовой пояс указан не верно")
            if "theme" in exc_text:
                raise DataFormatError("Оформление указано не верно")
            else:
                raise

    async def change_password(self, user_id: uuid.UUID, new_password_dto: UserPasswordUpdateSchema):
        current_password = new_password_dto.current_password.get_secret_value()
        new_password = new_password_dto.new_password.get_secret_value()

        new_password_hash = await create_password(password=new_password)

        if not new_password_hash:
            raise IncorrectPassword("Не удалось проверить пароли")

        user_dao = await self.repo.get_user_by_id(user_id=user_id)
        if not user_dao:
            raise UserNotFoundError("Пользователь не найден")

        is_password_correct = await verify_password(password=current_password, hashed_password=user_dao.password_hash)
        if not is_password_correct:
            raise IncorrectPassword("Текущий пароль не верный")

        user_dao.password_hash = new_password_hash
        await self.repo._commit()

        return await self._issue_tokens(user_dao)

    async def search_users(self, current_user_id: uuid.UUID, query: str, limit: int) -> list[UserSearchSchema]:
        users = await self.repo.search_users(query=query.strip().lower(), exclude_user_id=current_user_id, limit=limit)
        return [UserSearchSchema.model_validate(user) for user in users]
