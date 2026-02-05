"""Logging configuration for the API."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import get_settings

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def _ensure_handlers(logger: logging.Logger) -> None:
    settings = get_settings()
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(_LOG_FORMAT)

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def configure_logging() -> logging.Logger:
    """Configure root logger if not already set up."""
    logger = logging.getLogger("asset_api")
    if not logger.handlers:
        logger.setLevel(get_settings().log_level.upper())
        _ensure_handlers(logger)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger with the configured root as parent."""
    root_logger = configure_logging()
    if name:
        return root_logger.getChild(name)
    return root_logger
