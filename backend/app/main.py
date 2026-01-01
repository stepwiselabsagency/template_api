import os
import time
from contextlib import asynccontextmanager

import psycopg
import redis
from app.api.router import router as api_router
from fastapi import FastAPI


def _coerce_psycopg_dsn(database_url: str) -> str:
    # DATABASE_URL is commonly expressed as SQLAlchemy style:
    #   postgresql+psycopg://user:pass@host:port/db
    # psycopg expects:
    #   postgresql://user:pass@host:port/db
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def _best_effort_wait_for_deps() -> None:
    """
    Keep this minimal: try a few times and never crash-loop if deps aren't ready.
    """

    database_url = os.getenv("DATABASE_URL", "")
    redis_url = os.getenv("REDIS_URL", "")

    for _ in range(10):
        postgres_ok = True
        redis_ok = True

        if database_url:
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
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        _best_effort_wait_for_deps()
        yield

    app = FastAPI(title="backend", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)
    return app


app = create_app()
