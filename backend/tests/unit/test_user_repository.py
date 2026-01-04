from __future__ import annotations

import pytest
from app.repositories.user_repository import UserRepository
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@pytest.mark.unit
def test_user_repository_create_and_get_by_email(db_session: Session) -> None:
    repo = UserRepository(db_session)
    created = repo.create(email="repo-test@example.com", hashed_password="hash")

    fetched = repo.get_by_email("repo-test@example.com")
    assert fetched is not None
    assert fetched.id == created.id


@pytest.mark.unit
def test_user_repository_unique_email_constraint(db_session: Session) -> None:
    repo = UserRepository(db_session)
    repo.create(email="dup@example.com", hashed_password="hash")

    # Repo commits; a duplicate should surface as DB integrity error.
    with pytest.raises(IntegrityError):
        repo.create(email="dup@example.com", hashed_password="hash")
