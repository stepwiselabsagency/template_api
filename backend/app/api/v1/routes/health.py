from __future__ import annotations

import logging

import psycopg
import redis
from app.core.config import get_settings
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    """
    Liveness probe: indicates the process is running.
    """

    return {"status": "ok"}


def _coerce_psycopg_dsn(database_url: str) -> str:
    # DATABASE_URL is commonly expressed as SQLAlchemy style:
    #   postgresql+psycopg://user:pass@host:port/db
    # psycopg expects:
    #   postgresql://user:pass@host:port/db
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _check_db(database_url: str) -> bool:
    if not database_url:
        return False

    try:
        if database_url.startswith("postgres"):
            dsn = _coerce_psycopg_dsn(database_url)
            with psycopg.connect(dsn, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True

        # SQLite and other SQLAlchemy URLs
        from app.db.session import create_engine_from_settings

        settings = get_settings()
        settings = settings.model_copy(update={"DATABASE_URL": database_url})
        engine = create_engine_from_settings(settings)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except (SQLAlchemyError, Exception):
        return False


def _check_redis(redis_url: str) -> bool:
    if not redis_url:
        # Redis is part of the template, but allow readiness to pass if it's
        # not configured.
        return True

    try:
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        return bool(client.ping())
    except Exception:
        return False


@router.get("/ready")
def ready():
    """
    Readiness probe: indicates the app is ready to serve traffic.
    """

    settings = get_settings()
    db_ok = _check_db(settings.DATABASE_URL)
    redis_ok = _check_redis(settings.REDIS_URL)

    checks = {"db": "ok" if db_ok else "error", "redis": "ok" if redis_ok else "error"}
    if db_ok and redis_ok:
        return {"status": "ok", "checks": checks}

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "error", "checks": checks},
    )
