from __future__ import annotations

import os

from app.core.config import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_v1_health_live() -> None:
    app = create_app()
    client = TestClient(app)

    res = client.get("/api/v1/health/live")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    assert res.headers.get("X-Request-ID")


def test_v1_health_ready_returns_200_with_sqlite(tmp_path) -> None:
    # Opt into DB for readiness (default test env has DATABASE_URL empty).
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'db.sqlite'}"
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["checks"]["db"] == "ok"
    assert body["checks"]["redis"] == "ok"


def test_v1_health_ready_returns_503_when_db_not_configured() -> None:
    app = create_app()
    client = TestClient(app)

    res = client.get("/api/v1/health/ready")
    assert res.status_code == 503
    body = res.json()
    assert body["status"] == "error"
    assert body["checks"]["db"] == "error"
    assert body["checks"]["redis"] == "ok"


def test_v1_health_ready_returns_503_when_redis_unreachable(tmp_path) -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'db.sqlite'}"
    os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)

    res = client.get("/api/v1/health/ready")
    assert res.status_code == 503
    body = res.json()
    assert body["status"] == "error"
    assert body["checks"]["db"] == "ok"
    assert body["checks"]["redis"] == "error"
