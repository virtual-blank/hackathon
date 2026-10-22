from pathlib import Path
import logging
import re
import logging.config
from typing import Any

from core.config import LoggingSettings, get_logging_settings

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Уровни для сторонних библиотек: без них при LOG_LEVEL=DEBUG консоль тонет
# в чужих отладочных сообщениях и наши логи в ней не найти.
_PACKAGE_LOG_LEVELS: dict[str, str] = {
    # echo=False в database/db.py логи SQL не выключает — они идут по уровню root
    "sqlalchemy.engine": "WARNING",
    "botocore": "WARNING",
    "aiobotocore": "WARNING",
    "boto3": "WARNING",
    "httpx": "WARNING",
    "httpcore": "WARNING",
    "apscheduler": "WARNING",
    "python_multipart": "INFO",
    "passlib": "INFO",
}

class RedactWebSocketTokenFilter(logging.Filter):
    """Скрывает токены аутентификации в сообщениях логов."""

    _pattern = re.compile(r"(?i)(token=)[^&\s\"']+")

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted_message = self._pattern.sub(r"\1[REDACTED]", message)

        if redacted_message != message:
            record.msg = redacted_message
            record.args = ()

        return True


def logging_config(settings: LoggingSettings | None = None) -> dict[str, Any]:
    """Собирает словарь для `logging.config.dictConfig`.

    Один источник правды: его применяет `setup_logging`, и его же получает uvicorn
    через `log_config` — иначе под `reload=True` процесс-воркер uvicorn
    перенастроит логирование по-своему.
    """
    if settings is None:
        settings = get_logging_settings()

    return {
        "version": 1,
        # False — иначе dictConfig отключит логгеры, созданные до его вызова
        # (`logger = logging.getLogger(__name__)` на уровне модулей).
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": settings.format}},
        "filters": {
            "redact_websocket_token": {
                "()": RedactWebSocketTokenFilter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "filters": ["redact_websocket_token"],
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(LOG_FILE),
                "encoding": "utf-8",
                "maxBytes": 1_000_000,
                "backupCount": 3,
                "formatter": "default",
                "filters": ["redact_websocket_token"],
            }
        },
        "loggers": {name: {"level": level} for name, level in _PACKAGE_LOG_LEVELS.items()},
        "root": {"level": settings.level, "handlers": ["console", "file"]},
    }


def setup_logging(settings: LoggingSettings | None = None) -> None:
    logging.config.dictConfig(logging_config(settings))