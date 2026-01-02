from __future__ import annotations

from datetime import timedelta

from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.core.config import get_settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def issue_token_for_user(user: User) -> dict[str, object]:
    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES)
    access_token = create_access_token(
        str(user.id),
        expires_delta=access_token_expires,
        additional_claims={
            # Minimal "roles" claim for template RBAC.
            "roles": ["admin"] if getattr(user, "is_superuser", False) else [],
        },
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
    }
