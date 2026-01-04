from __future__ import annotations

import os
from pathlib import Path

# Ensure models are registered on Base.metadata for create_all() and migrations.
import app.models  # noqa: F401  (import side-effects)
import pytest
from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from app.db.base import Base
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def _is_postgres(database_url: str) -> bool:
    return database_url.startswith("postgresql://") or database_url.startswith(
        "postgresql+"
    )


@pytest.fixture(scope="session")
def database_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    """
    Database URL used by db fixtures.

    - In CI, `DATABASE_URL` is expected to point at the Postgres service.
    - Locally, we default to a temporary SQLite file for hermetic tests.
    """
    env_url = os.getenv("DATABASE_URL") or ""
    if env_url:
        return env_url
    db_path = tmp_path_factory.mktemp("db") / "test.sqlite"
    return f"sqlite:///{db_path}"


@pytest.fixture(scope="session")
def db_engine(database_url: str) -> Engine:
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


@pytest.fixture(scope="session")
def db_schema(db_engine: Engine, database_url: str) -> None:
    """
    Ensure the database schema exists once per test session.

    - For Postgres: run Alembic migrations (matches production behavior).
    - For SQLite fallback: use SQLAlchemy metadata to stay hermetic.
      (Current migrations include Postgres-only SQL like `now()`.)
    """
    if _is_postgres(database_url):
        os.environ["DATABASE_URL"] = database_url
        get_settings.cache_clear()

        alembic_ini = Path("backend/alembic.ini")
        cfg = Config(str(alembic_ini))
        command.upgrade(cfg, "head")
    else:
        Base.metadata.create_all(bind=db_engine)


@pytest.fixture()
def db_session(db_engine: Engine, db_schema: None) -> Session:
    """
    Provide a DB session wrapped in a rollback-only nested transaction.
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(
        bind=connection,
        class_=Session,
        expire_on_commit=False,
        autoflush=False,
    )
    session = SessionLocal()

    # IMPORTANT:
    # Repository code calls `Session.commit()`. For tests we want commit to be
    # rollback-only (per test), so we make commit a flush. The outer connection
    # transaction is rolled back in fixture teardown.
    original_commit = session.commit

    def _commit() -> None:
        session.flush()

    session.commit = _commit  # type: ignore[method-assign]

    try:
        yield session
    finally:
        session.commit = original_commit  # type: ignore[method-assign]
        try:
            session.rollback()
        except Exception:
            pass
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
