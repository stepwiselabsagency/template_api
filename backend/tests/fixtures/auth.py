from __future__ import annotations

import pytest
from app.auth.password import hash_password
from app.repositories.user_repository import UserRepository
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture()
def test_user(db_session: Session):
    """
    Create an active user with a known password for auth-related tests.
    """
    return UserRepository(db_session).create(
        email="test@example.com",
        hashed_password=hash_password("pass123"),
        is_active=True,
    )


@pytest.fixture()
def auth_headers(client: TestClient, test_user) -> dict[str, str]:
    """
    Log in as `test_user` and return Authorization headers.
    """
    res = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "pass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
