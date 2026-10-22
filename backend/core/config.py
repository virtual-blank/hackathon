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
    refresh_token_expire_days: int = 30

class MinioSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="MINIO_", extra="ignore")
    host: str
    port: int
    root_user: str
    root_password: str
    bucket_name: str
    endpoint: str
    public_url: str = ""  # Публичный URL для presigned links и префиксов; если пусто, используется endpoint
    protocol: str = "http"
    ttl_link_sec: int = 300
    
    @property
    def effective_public_url(self) -> str:
        """Возвращает public_url если задан, иначе endpoint (обратная совместимость)"""
        return self.public_url if self.public_url else self.endpoint


class TelegramSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="TELEGRAM_", extra="ignore")
    bot_token: str
    bot_name: str
    webhook_url: str = ""    #заполню позже
    link_ttl_minutes: int = 15

class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="LOG_", extra="ignore")
    level: str = "INFO"
    format: str = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

@lru_cache
def get_logging_settings() -> LoggingSettings:
    return LoggingSettings()

@lru_cache
def get_telegram_settings() -> TelegramSettings:
    return TelegramSettings()

@lru_cache
def get_db_settings() -> PostgresSettings:
    return PostgresSettings()


@lru_cache
def get_jwt_settings() -> JwtSettings:
    return JwtSettings()


@lru_cache
def get_minio_settings() -> MinioSettings:
    return MinioSettings()
