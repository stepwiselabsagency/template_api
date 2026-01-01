from __future__ import annotations

from functools import lru_cache
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _redact_url_secret(url: str) -> str:
    """
    Best-effort redaction for URLs that may embed credentials.

    Examples:
      postgresql://user:pass@host/db -> postgresql://user:***@host/db
      redis://:pass@host/0          -> redis://:***@host/0
    """
    if not url:
        return url

    try:
        parts = urlsplit(url)
    except Exception:
        return "***"

    if "@" not in (parts.netloc or ""):
        return url

    userinfo, hostinfo = parts.netloc.rsplit("@", 1)
    if ":" not in userinfo:
        # user@host (no password) -> safe enough
        return url

    user, _password = userinfo.split(":", 1)
    redacted_netloc = f"{user}:***@{hostinfo}"
    return urlunsplit(
        (parts.scheme, redacted_netloc, parts.path, parts.query, parts.fragment)
    )


class Settings(BaseSettings):
    """
    Central configuration for the application.

    Values load from environment variables and (for local dev) an optional `.env`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    ENV: str = Field(default="local", validation_alias=AliasChoices("ENV", "APP_ENV"))
    DEBUG: bool = False

    APP_NAME: str = "backend"
    API_PREFIX: str = ""

    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # Keep these empty by default so local unit tests don't attempt to connect.
    # Docker Compose sets them explicitly.
    DATABASE_URL: str = ""
    REDIS_URL: str = ""

    CORS_ALLOW_ORIGINS: list[str] = []

    def model_dump_safe(self) -> dict[str, Any]:
        """
        Safe-to-log view of settings (redacts secrets).
        """
        data = self.model_dump()
        data["DATABASE_URL"] = _redact_url_secret(str(data.get("DATABASE_URL") or ""))
        data["REDIS_URL"] = _redact_url_secret(str(data.get("REDIS_URL") or ""))
        return data


@lru_cache
def get_settings() -> Settings:
    return Settings()
