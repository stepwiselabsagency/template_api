from __future__ import annotations

import uuid

from pydantic import BaseModel


class UserCreateRequest(BaseModel):
    # Keep this as `str` to avoid requiring `email-validator` in the base template.
    # Projects that need strict email validation can switch to `EmailStr`.
    email: str
    password: str


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    is_superuser: bool = False
