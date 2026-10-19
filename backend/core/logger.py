import logging.config
from typing import Any

from core.config import LoggerSettings, get_logger_settings

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


def logging_config(settings: LoggerSettings | None = None) -> dict[str, Any]:
    """Собирает словарь для `logging.config.dictConfig`.

    Один источник правды: его применяет `setup_logging`, и его же получает uvicorn
    через `log_config` — иначе под `reload=True` процесс-воркер uvicorn
    перенастроит логирование по-своему.
    """
    if settings is None:
        settings = get_logger_settings()

    return {
        "version": 1,
        # False — иначе dictConfig отключит логгеры, созданные до его вызова
        # (`logger = logging.getLogger(__name__)` на уровне модулей).
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": settings.format}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "loggers": {name: {"level": level} for name, level in _PACKAGE_LOG_LEVELS.items()},
        "root": {"level": settings.level, "handlers": ["console"]},
    }


def setup_logging(settings: LoggerSettings | None = None) -> None:
    logging.config.dictConfig(logging_config(settings))
