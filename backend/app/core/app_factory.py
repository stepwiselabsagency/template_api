from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

import psycopg
import redis
from app.api.router import router as api_router
from app.api.v1.router import v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware, RequestLoggingMiddleware
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

log = logging.getLogger(__name__)


def _coerce_psycopg_dsn(database_url: str) -> str:
    # DATABASE_URL is commonly expressed as SQLAlchemy style:
    #   postgresql+psycopg://user:pass@host:port/db
    # psycopg expects:
    #   postgresql://user:pass@host:port/db
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _best_effort_wait_for_deps(*, database_url: str, redis_url: str) -> None:
    """
    Keep this minimal: try a few times and never crash-loop if deps aren't ready.
    """
    if not database_url and not redis_url:
        return

    for _ in range(10):
        postgres_ok = True
        redis_ok = True

        if database_url and database_url.startswith("postgres"):
            try:
                dsn = _coerce_psycopg_dsn(database_url)
                with psycopg.connect(dsn, connect_timeout=2):
                    pass
            except Exception:
                postgres_ok = False

        if redis_url:
            try:
                client = redis.Redis.from_url(redis_url, socket_connect_timeout=2)
                client.ping()
            except Exception:
                redis_ok = False

        if postgres_ok and redis_ok:
            return

        time.sleep(1)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        _best_effort_wait_for_deps(
            database_url=settings.DATABASE_URL, redis_url=settings.REDIS_URL
        )
        yield

    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware order matters:
    # - CORS should be outermost (when enabled)
    # - request id runs before request logging so all logs get a request_id
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware, settings=settings)

    if settings.CORS_ALLOW_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOW_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Versioned public API baseline
    app.include_router(v1_router)

    app.include_router(api_router, prefix=settings.API_PREFIX)

    log.info("app created")
    return app
