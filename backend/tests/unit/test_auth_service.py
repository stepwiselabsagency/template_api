from __future__ import annotations

import pytest
from app.auth.password import hash_password
from app.auth.service import authenticate_user
from app.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session


@pytest.mark.unit
def test_authenticate_user_returns_user_for_valid_credentials(
    db_session: Session,
) -> None:
    UserRepository(db_session).create(
        email="test@example.com",
        hashed_password=hash_password("pass123"),
        is_active=True,
    )
    user = authenticate_user(db_session, "test@example.com", "pass123")
    assert user is not None
    assert user.email == "test@example.com"


@pytest.mark.unit
def test_authenticate_user_returns_none_for_invalid_credentials(
    db_session: Session,
) -> None:
    UserRepository(db_session).create(
        email="test@example.com",
        hashed_password=hash_password("pass123"),
        is_active=True,
    )
    user = authenticate_user(db_session, "test@example.com", "wrong")
    assert user is None


@pytest.mark.unit
def test_authenticate_user_inactive_user_cannot_authenticate(
    db_session: Session,
) -> None:
    UserRepository(db_session).create(
        email="test@example.com",
        hashed_password=hash_password("pass123"),
        is_active=False,
    )
    user = authenticate_user(db_session, "test@example.com", "pass123")
    assert user is None
