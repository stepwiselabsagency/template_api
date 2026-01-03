from __future__ import annotations

import app.models  # noqa: F401  (import side-effects)
from app.core.config import Settings
from app.db import Base, get_db
from app.db.session import create_engine_from_settings
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


def test_standard_error_schema_for_404_under_v1() -> None:
    app = create_app()
    client = TestClient(app)

    res = client.get("/api/v1/does-not-exist")
    assert res.status_code == 404
    assert res.headers.get("X-Request-ID")

    body = res.json()
    assert set(body.keys()) == {"error"}
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"]
    assert body["error"]["request_id"] == res.headers["X-Request-ID"]


def test_standard_error_schema_for_422_validation_error() -> None:
    # Use sqlite to keep DB dependency hermetic for this validation test.
    settings = Settings(DATABASE_URL="sqlite://")
    engine = create_engine_from_settings(settings)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    app = create_app()

    def override_get_db():
        with SessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    res = client.post("/api/v1/users", json={"email": "test@example.com"})
    assert res.status_code == 422
    assert res.headers.get("X-Request-ID")

    body = res.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["request_id"] == res.headers["X-Request-ID"]
    assert isinstance(body["error"]["details"], list)
