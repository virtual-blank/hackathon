import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

from src.achievements.schemas import AchievementOutputSchema
from src.users.enums import Theme, TimezoneEnum
from src.users.pfp.minio import DEFAULT_PFP_URL


class UserCreateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: Annotated[str, Field(min_length=5, max_length=16, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")]
    password: SecretStr
    email: EmailStr

    @field_validator("username")
    @classmethod
    def username_lowercase(cls, v: str) -> str:
        return v.lower()


class UserLoginSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    username: Annotated[str, Field(min_length=5, max_length=16)]
    password: SecretStr

    @field_validator("username")
    @classmethod
    def username_lowercase(cls, v: str) -> str:
        return v.lower()


class UserUpdateSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr | None = None
    username: Annotated[str, Field(min_length=5, max_length=16, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")] | None = None
    timezone: TimezoneEnum | None = None
    theme: Theme | None = None

    @field_validator("username")
    @classmethod
    def username_lowercase(cls, v: str | None) -> str | None:
        return v.lower() if v else None


class UserPasswordUpdateSchema(BaseModel):
    current_password: SecretStr
    new_password: SecretStr


class UserOutputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    username: str
    email: EmailStr
    theme: Theme
    timezone: str
    telegram_chat_id: int | None = None
    pfp_url: str
    achievements: list[AchievementOutputSchema] = []

    @field_validator("pfp_url", mode="before")
    @classmethod
    def set_default_pfp(cls, v: str | None) -> str:
        return v or DEFAULT_PFP_URL

    @field_validator("achievements", mode="before")
    @classmethod
    def extract_achievements(cls, v: Any) -> list[Any]:
        if not v:
            return []
        return [
            item.achievement if hasattr(item, "achievement") else item
            for item in v
            if getattr(item, "achievement", item) is not None
        ]


class UserSearchSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    pfp_url: str

    @field_validator("pfp_url", mode="before")
    @classmethod
    def set_default_pfp(cls, v: str | None) -> str:
        return v or DEFAULT_PFP_URL


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    refresh_token: str


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class AuthOutputSchema(BaseModel):
    user: UserOutputSchema
    token: TokenSchema
