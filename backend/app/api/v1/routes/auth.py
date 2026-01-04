from __future__ import annotations

import uuid

from app.auth.dependencies import get_current_user
from app.auth.service import authenticate_user, issue_token_for_user
from app.db import get_db
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    is_superuser: bool = False


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    # OAuth2PasswordRequestForm uses `username`; we treat it as email in this template.
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise _invalid_credentials()
    return TokenResponse(**issue_token_for_user(user))


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        is_superuser=getattr(current_user, "is_superuser", False),
    )
