import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

from src.users.enums import AvatarContentType


class UserCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: Annotated[str, Field(min_length=5, max_length=16)]
    password: SecretStr
    email: EmailStr

    @field_validator("username")
    @classmethod
    def username_check(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Имя пользователя должно содержать только буквы или цифры")
        return v.lower()


class UserLoginSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: Annotated[str, Field(min_length=5, max_length=16)]
    password: SecretStr

    @field_validator("username")
    @classmethod
    def username_check(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Имя пользователя должно содержать только буквы или цифры")
        return v.lower()


class UserUpdateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: str | None = None
    password: SecretStr | None = None
    pfp_url: str | None = None


class UserOutputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    username: str
    email: EmailStr
    telegram_chat_id: int | None = None
    # todo: добавить позже pfp_url: str | None = None | ссылка на фотку профиля (minio)


class AvatarUploadCreateSchema(BaseModel):
    content_type: AvatarContentType


class AvatarUploadOutputSchema(BaseModel):
    upload_url: str
    key: str
    content_type: AvatarContentType
    expires_in_sec: int


class AvatarSetSchema(BaseModel):
    key: Annotated[str, Field(min_length=1, max_length=255)]


class AvatarOutputSchema(BaseModel):
    pfp_url: str
    expires_in_sec: int


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class AuthOutputSchema(BaseModel):
    user: UserOutputSchema
    token: TokenSchema
