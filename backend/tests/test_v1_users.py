from __future__ import annotations

# Ensure models are registered on Base.metadata for create_all().
import app.models  # noqa: F401  (import side-effects)
from app.core.config import Settings
from app.db import Base, get_db
from app.db.session import create_engine_from_settings
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


def test_v1_user_create_login_and_me(tmp_path) -> None:
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

    # Create users (v1)
    res = client.post(
        "/api/v1/users",
        json={"email": "test@example.com", "password": "pass123"},
    )
    assert res.status_code == 201
    created = res.json()
    assert created["email"] == "test@example.com"
    assert created["id"]

    other = client.post(
        "/api/v1/users",
        json={"email": "other@example.com", "password": "pass123"},
    )
    assert other.status_code == 201
    other_body = other.json()

    dup = client.post(
        "/api/v1/users",
        json={"email": "test@example.com", "password": "pass123"},
    )
    assert dup.status_code == 409

    # Login (v1)
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "pass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    # Me (v1)
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.headers.get("X-Request-ID")
    me_body = me.json()
    assert me_body["email"] == "test@example.com"
    assert me_body["id"] == created["id"]

    # Authorization: cannot fetch someone else's user unless superuser
    other_res = client.get(
        f"/api/v1/users/{other_body['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert other_res.status_code == 403

    self_res = client.get(
        f"/api/v1/users/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert self_res.status_code == 200
