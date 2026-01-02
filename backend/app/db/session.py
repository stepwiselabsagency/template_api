from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_engine_from_settings(settings: Settings) -> Engine:
    """
    Create a SQLAlchemy engine from app settings.

    Notes:
    - Engine creation does not establish a DB connection; connections are opened
      lazily when first used.
    - We keep SQLite handling minimal and only for local/dev/test convenience.
    """

    url = settings.DATABASE_URL

    connect_args: dict[str, object] = {}
    if url.startswith("sqlite"):
        # Needed for SQLite when using FastAPI/TestClient across threads.
        connect_args["check_same_thread"] = False

    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


@lru_cache
def _get_engine() -> Engine:
    settings = get_settings()
    if not settings.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set DATABASE_URL in the environment."
        )
    return create_engine_from_settings(settings)


SessionLocal = sessionmaker(
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Session:
    """
    FastAPI dependency that provides a SQLAlchemy session per request.
    """

    # Bind lazily so importing app code doesn't require a configured DB.
    db = SessionLocal(bind=_get_engine())
    try:
        yield db
    finally:
        db.close()


def get_engine() -> Engine:
    """
    Accessor for the app's singleton Engine.

    Useful for scripts, health checks, and tests (without importing private helpers).
    """

    return _get_engine()
