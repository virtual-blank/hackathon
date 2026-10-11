from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="POSTGRES_", extra="ignore")
    user: str
    password: str
    host: str
    port: int
    name: str

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class JwtSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="JWT_", extra="ignore")
    access_token_expire_minutes: int
    secret_key: str
    algorithm: str


class MinioSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="MINIO_", extra="ignore")
    host: str
    port: int
    root_user: str
    root_password: str
    bucket_name: str
    
    @property
    def endpoint(self) -> str:
        return f"http://{self.host}:{self.port}"


@lru_cache
def get_db_settings() -> PostgresSettings:
    return PostgresSettings()


@lru_cache
def get_jwt_settings() -> JwtSettings:
    return JwtSettings()


@lru_cache
def get_minio_settings() -> MinioSettings:
    return MinioSettings()
