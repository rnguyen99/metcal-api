"""Application configuration utilities."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings:
    """Simple settings object sourced from environment variables."""

    def __init__(self) -> None:
        self.secret_key = os.getenv("SECRET_KEY", "change-me")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_hours = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
        self.database_path = os.getenv("DATABASE_PATH", str(BASE_DIR / "asset.db"))
        self.cors_allow_origins = self._parse_origins(os.getenv("CORS_ALLOW_ORIGINS", "*"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "api.log"))

    @staticmethod
    def _parse_origins(value: str) -> list[str]:
        value = value.strip()
        if value == "*" or not value:
            return ["*"]
        return [origin.strip() for origin in value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cache Settings instance for reuse."""
    return Settings()
