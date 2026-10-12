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
    protocol: str = "http"
    ttl_link_sec: int = 300

    @property
    def endpoint(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"


class RedisSettings(BaseSettings):
    """
    Подключение к Redis. Пропуска для вебсокета лежат там, а не в памяти процесса,
    чтобы приложение можно было запускать в несколько воркеров.
    """

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="REDIS_", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0
    password: str | None = None

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


@lru_cache
def get_db_settings() -> PostgresSettings:
    return PostgresSettings()


@lru_cache
def get_jwt_settings() -> JwtSettings:
    return JwtSettings()


@lru_cache
def get_minio_settings() -> MinioSettings:
    return MinioSettings()


@lru_cache
def get_redis_settings() -> RedisSettings:
    return RedisSettings()
