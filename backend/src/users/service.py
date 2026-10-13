import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.hash_argon import DUMMY_HASH, create_password, verify_password
from src.auth.security import create_access_token
from src.users.repository import UsersRepository
from src.users.schemas import AuthOutputSchema, TokenSchema, UserCreateSchema, UserLoginSchema, UserOutputSchema


class UsersService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UsersRepository(session=session)

    async def sign_up(self, user_data: UserCreateSchema):
        password = user_data.password.get_secret_value()
        password_hash = await create_password(password=password)
        try:
            new_user_dao = await self.repo.create_user(
                username=user_data.username, password_hash=password_hash, email=user_data.email
            )
            token_str = create_access_token(user_id=new_user_dao.id)
            token_jwt = TokenSchema(access_token=token_str)
            return AuthOutputSchema(user=UserOutputSchema.model_validate(new_user_dao), token=token_jwt)
        except IntegrityError as e:
            if "username" in str(e.orig):
                raise ValueError("Этот юзернейм занят")
            if "email" in str(e.orig):
                raise ValueError("Этот email уже зарегистрирован")

    async def login(self, user_data: UserLoginSchema):
        password = user_data.password.get_secret_value()
        user_dao = await self.repo.get_user_by_username(username=user_data.username)
        if not user_dao:
            await verify_password(
                password=password, hashed_password=DUMMY_HASH
            )  # предотвращение утечки никнеймов по времени ответа сервера
            raise ValueError("Неверный логин или пароль")
        is_password_correct = await verify_password(password=password, hashed_password=user_dao.password_hash)
        if not is_password_correct:
            raise ValueError("Неверный логин или пароль")
        token_str = create_access_token(user_id=user_dao.id)
        token_jwt = TokenSchema(access_token=token_str)
        return AuthOutputSchema(user=UserOutputSchema.model_validate(user_dao), token=token_jwt)
    
    async def delete_account(self, user_id: uuid.UUID) -> None:
        deleted = await self.repo.delete_user(user_id=user_id)
        if not deleted:
            raise ValueError("Пользователь не найден")