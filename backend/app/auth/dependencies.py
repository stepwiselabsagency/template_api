from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from app.auth.jwt import decode_token
from app.db import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Canonical public auth endpoint lives under /api/v1.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_token_payload(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    try:
        payload = decode_token(token)
    except Exception:
        raise _unauthorized()
    return payload


def get_current_user(
    payload: dict[str, Any] = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:
    sub = payload.get("sub")
    try:
        user_id = uuid.UUID(str(sub))
    except Exception:
        raise _unauthorized()

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise _unauthorized()
    return user


require_user = get_current_user


def _roles_from_user(user: User) -> set[str]:
    # Minimal template RBAC: map is_superuser -> "admin".
    if getattr(user, "is_superuser", False):
        return {"admin"}
    return set()


def _roles_from_token(payload: dict[str, Any]) -> set[str]:
    raw = payload.get("roles")
    if not raw:
        return set()
    if isinstance(raw, list) and all(isinstance(r, str) for r in raw):
        return set(raw)
    return set()


def require_roles(*roles: str) -> Callable[..., User]:
    required = {r for r in roles if r}

    def _dep(
        user: User = Depends(get_current_user),
        payload: dict[str, Any] = Depends(get_token_payload),
    ) -> User:
        token_roles = _roles_from_token(payload)
        user_roles = _roles_from_user(user)
        effective = token_roles | user_roles
        if required and not (effective & required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return user

    return _dep
