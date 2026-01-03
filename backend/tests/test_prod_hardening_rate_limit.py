from __future__ import annotations

import app.models  # noqa: F401  (import side-effects)
import pytest
from app.core.config import Settings, get_settings
from app.db import Base, get_db
from app.db.session import create_engine_from_settings
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


def test_rate_limit_disabled_does_not_add_headers(tmp_path) -> None:
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'db.sqlite'}")
    engine = create_engine_from_settings(settings)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    app = create_app()

    def override_get_db():
        with SessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    res = client.get("/api/v1/health/live")
    assert res.status_code == 200
    assert "X-RateLimit-Limit" not in res.headers


def test_rate_limit_enabled_returns_429_and_headers(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    get_settings.cache_clear()

    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'db.sqlite'}")
    engine = create_engine_from_settings(settings)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    app = create_app()

    def override_get_db():
        with SessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    r1 = client.post(
        "/api/v1/users",
        json={"email": "u1@example.com", "password": "pass123"},
    )
    assert r1.status_code == 201
    assert r1.headers.get("X-RateLimit-Limit") == "2"

    r2 = client.post(
        "/api/v1/users",
        json={"email": "u2@example.com", "password": "pass123"},
    )
    assert r2.status_code == 201
    assert int(r2.headers["X-RateLimit-Remaining"]) >= 0

    r3 = client.post(
        "/api/v1/users",
        json={"email": "u3@example.com", "password": "pass123"},
    )
    assert r3.status_code == 429
    body = r3.json()
    assert body["error"]["code"] == "rate_limited"
    assert r3.headers.get("X-RateLimit-Reset")
