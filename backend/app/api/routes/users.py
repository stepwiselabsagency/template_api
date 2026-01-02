from __future__ import annotations

import uuid

from app.core.security import hash_password
from app.db import get_db
from app.repositories.user_repository import UserRepository
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    # Keep this as `str` to avoid requiring `email-validator` in the base template.
    # Projects that need strict email validation can switch to `EmailStr`.
    email: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest, db: Session = Depends(get_db)
) -> UserResponse:
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
    return UserResponse(id=user.id, email=user.email, is_active=user.is_active)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> UserResponse:
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return UserResponse(id=user.id, email=user.email, is_active=user.is_active)
