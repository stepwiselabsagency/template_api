from __future__ import annotations

import json
import uuid

from app.api.v1.schemas.users import UserCreateRequest, UserPublic
from app.auth.dependencies import get_current_user
from app.core.cache.dependency import get_cache
from app.core.cache.interface import Cache
from app.core.config import get_settings
from app.core.security import hash_password
from app.db import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["users"])


def _to_user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=getattr(user, "is_superuser", False),
    )


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
) -> UserPublic:
    repo = UserRepository(db)
    if "@" not in payload.email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="invalid email"
        )
    existing = repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email already exists"
        )

    user = repo.create(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    return _to_user_public(user)


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return _to_user_public(current_user)


@router.get("/{user_id}", response_model=UserPublic)
def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cache: Cache = Depends(get_cache),
) -> UserPublic:
    if current_user.id != user_id and not getattr(current_user, "is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    settings = get_settings()
    cache_key = f"users:{user_id}"
    cached = cache.get(cache_key) if settings.CACHE_ENABLED else None
    if cached:
        try:
            data = json.loads(cached)
            return UserPublic(**data)
        except Exception:
            # Fail open (cache corruption/unexpected value); fall back to DB.
            pass

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    public = _to_user_public(user)

    if settings.CACHE_ENABLED:
        ttl = min(int(settings.CACHE_DEFAULT_TTL_SECONDS), 60)
        cache.set(cache_key, public.model_dump_json(), ttl_seconds=ttl)

    return public
