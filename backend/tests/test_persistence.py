from __future__ import annotations

import time

# Ensure models are registered on Base.metadata for create_all().
import app.models  # noqa: F401  (import side-effects)
from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_engine_from_settings
from app.repositories.user_repository import UserRepository
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker


def _wait_for_db(engine: Engine, *, timeout_s: float = 15.0) -> None:
    deadline = time.time() + timeout_s
    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.5)


def test_user_repository_create_and_get(tmp_path) -> None:
    # Keep unit tests hermetic and environment-independent:
    # use SQLite by default (fast, no external services).
    database_url = f"sqlite:///{tmp_path / 'test.db'}"

    settings = Settings(DATABASE_URL=database_url)
    engine = create_engine_from_settings(settings)

    _wait_for_db(engine)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    with SessionLocal() as db:
        repo = UserRepository(db)
        user = repo.create(email="repo-test@example.com", hashed_password="hash")
        fetched = repo.get_by_id(user.id)

        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.email == "repo-test@example.com"
