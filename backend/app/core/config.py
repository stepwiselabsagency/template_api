from __future__ import annotations

from functools import lru_cache
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from pydantic import AliasChoices, Field, model_validator
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

    # --- Auth / JWT ---
    # Default is OK for local dev; must be overridden outside local/test.
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PROD"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES: int = 60
    JWT_ISSUER: str = ""
    JWT_AUDIENCE: str = ""

    @model_validator(mode="after")
    def _validate_security_settings(self) -> "Settings":
        if self.ENV not in {"local", "test"}:
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == "CHANGE_ME_IN_PROD":
                raise ValueError(
                    "JWT_SECRET_KEY must be set to a strong secret outside local/test."
                )
        return self

    def model_dump_safe(self) -> dict[str, Any]:
        """
        Safe-to-log view of settings (redacts secrets).
        """
        data = self.model_dump()
        data["DATABASE_URL"] = _redact_url_secret(str(data.get("DATABASE_URL") or ""))
        data["REDIS_URL"] = _redact_url_secret(str(data.get("REDIS_URL") or ""))
        if data.get("JWT_SECRET_KEY"):
            data["JWT_SECRET_KEY"] = "***"
        return data


@lru_cache
def get_settings() -> Settings:
    return Settings()
