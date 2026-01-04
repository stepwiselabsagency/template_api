from __future__ import annotations

# Ensure models are registered on Base.metadata for create_all().
import app.models  # noqa: F401  (import side-effects)
from app.auth.password import hash_password
from app.core.config import Settings, get_settings
from app.db import Base, get_db
from app.db.session import create_engine_from_settings
from app.main import create_app
from app.repositories.user_repository import UserRepository
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker


def _make_sqlite_engine(tmp_path) -> Engine:
    # Use file-based SQLite so multiple sessions can see the same DB state.
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'db.sqlite'}")
    return create_engine_from_settings(settings)


def test_login_success_and_me(tmp_path) -> None:
    engine = _make_sqlite_engine(tmp_path)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    with SessionLocal() as db:
        user = UserRepository(db).create(
            email="test@example.com",
            hashed_password=hash_password("pass123"),
            is_active=True,
        )

    app = create_app()

    def override_get_db():
        with SessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    res = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "pass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] == get_settings().JWT_ACCESS_TOKEN_EXPIRES_MINUTES * 60

    token = body["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    me_body = me.json()
    assert me_body["id"] == str(user.id)
    assert me_body["email"] == "test@example.com"


def test_login_wrong_password_returns_401(tmp_path) -> None:
    engine = _make_sqlite_engine(tmp_path)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    with SessionLocal() as db:
        UserRepository(db).create(
            email="test@example.com",
            hashed_password=hash_password("pass123"),
            is_active=True,
        )

    app = create_app()

    def override_get_db():
        with SessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    res = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 401
    assert res.headers.get("WWW-Authenticate") == "Bearer"
