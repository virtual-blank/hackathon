import logging
import uuid

from core import storage
from core.config import get_minio_settings
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.hash_argon import DUMMY_HASH, create_password, verify_password
from src.auth.security import create_access_token
from src.exceptions.avatar_exceptions import AvatarFileNotFoundError, AvatarNotFoundError, AvatarTooLargeError
from src.users.enums import AvatarContentType
from src.users.models import User
from src.users.repository import UsersRepository
from src.users.schemas import (
    AuthOutputSchema,
    AvatarOutputSchema,
    AvatarUploadOutputSchema,
    TokenSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserOutputSchema,
)

logger = logging.getLogger(__name__)

MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024
AVATAR_EXTENSIONS = {
    AvatarContentType.JPEG: "jpg",
    AvatarContentType.PNG: "png",
    AvatarContentType.WEBP: "webp",
}


async def delete_stored_avatar(key: str) -> None:
    """Запись в БД уже обновлена, поэтому сбой хранилища не должен ронять запрос:
    файл останется лежать без ссылки на него, а пользователь получит успешный ответ."""
    try:
        await storage.delete_object(key)
    except storage.STORAGE_ERRORS:
        logger.exception("users: не удалось удалить файл аватара %s", key)


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

    async def create_avatar_upload(self, user: User, content_type: AvatarContentType) -> AvatarUploadOutputSchema:
        """Шаг 1 загрузки: выдаём ссылку, по которой клиент сам кладёт файл в хранилище.

        В БД ничего не пишем: файл ещё не загружен, и неизвестно, загрузят ли его вообще.
        """
        # Ключ начинается с id пользователя — по нему set_avatar проверяет, чей это файл.
        # Случайная часть нужна, чтобы новая загрузка не затёрла действующий аватар до подтверждения.
        key = f"{user.id}/{uuid.uuid4()}.{AVATAR_EXTENSIONS[content_type]}"
        upload_url = await storage.create_upload_url(key=key, content_type=content_type.value)
        return AvatarUploadOutputSchema(
            upload_url=upload_url,
            key=key,
            content_type=content_type,
            expires_in_sec=get_minio_settings().ttl_link_sec,
        )

    async def set_avatar(self, user: User, key: str) -> AvatarOutputSchema:
        """Шаг 2 загрузки: клиент сообщает, что файл загружен. Работает и для первого фото, и для замены."""
        if not key.startswith(f"{user.id}/"):
            raise AvatarFileNotFoundError("Файл не найден")

        size = await storage.find_object_size(key)
        if size is None:
            raise AvatarFileNotFoundError("Файл не найден")
        if size > MAX_AVATAR_SIZE_BYTES:
            # Presigned PUT не умеет ограничивать размер, поэтому проверяем после загрузки.
            await delete_stored_avatar(key)
            raise AvatarTooLargeError("Файл больше 5 МБ")

        old_key = user.pfp_key
        await self.repo.update_pfp_key(user=user, pfp_key=key)
        if old_key is not None and old_key != key:
            await delete_stored_avatar(old_key)
        return await self.get_avatar(user)

    async def get_avatar(self, user: User) -> AvatarOutputSchema:
        if user.pfp_key is None:
            raise AvatarNotFoundError("Фото профиля не установлено")
        return AvatarOutputSchema(
            pfp_url=await storage.create_download_url(user.pfp_key),
            expires_in_sec=get_minio_settings().ttl_link_sec,
        )

    async def delete_avatar(self, user: User) -> None:
        if user.pfp_key is None:
            raise AvatarNotFoundError("Фото профиля не установлено")
        old_key = user.pfp_key
        # Сначала БД, потом файл: при сбое между шагами останется лишний файл,
        # а не запись, которая ссылается на удалённый.
        await self.repo.update_pfp_key(user=user, pfp_key=None)
        await delete_stored_avatar(old_key)
