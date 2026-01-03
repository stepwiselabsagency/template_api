from __future__ import annotations

import app.models  # noqa: F401  (import side-effects)
import pytest
from app.core.cache.in_memory import InMemoryCache
from app.core.config import Settings, get_settings
from app.db import Base, get_db
from app.db.session import create_engine_from_settings
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


def test_cache_enabled_caches_get_user_by_id(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CACHE_ENABLED", "true")
    monkeypatch.setenv("CACHE_DEFAULT_TTL_SECONDS", "300")
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

    # Create a user (v1)
    res = client.post(
        "/api/v1/users",
        json={"email": "test@example.com", "password": "pass123"},
    )
    assert res.status_code == 201
    user_id = res.json()["id"]

    # Login (legacy)
    login = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "pass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    r1 = client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 200

    cache = app.state.cache
    assert isinstance(cache, InMemoryCache)
    assert f"cache:users:{user_id}" in cache._data  # noqa: SLF001 (test-only)

    r2 = client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
