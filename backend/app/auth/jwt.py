from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from app.core.config import get_settings

_DEFAULT_LEEWAY_SECONDS = 30


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    subject: str,
    *,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()

    if not subject or not isinstance(subject, str):
        raise ValueError("subject must be a non-empty string")

    now = _utcnow()
    expires = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES)
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }

    if settings.JWT_ISSUER:
        payload["iss"] = settings.JWT_ISSUER
    if settings.JWT_AUDIENCE:
        payload["aud"] = settings.JWT_AUDIENCE

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()

    if not token:
        raise ValueError("token must not be empty")

    options = {
        "require": ["exp", "sub", "iat"],
        "verify_signature": True,
        "verify_exp": True,
        "verify_iat": True,
        "verify_nbf": True,
        "verify_iss": bool(settings.JWT_ISSUER),
        "verify_aud": bool(settings.JWT_AUDIENCE),
    }

    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.JWT_ISSUER or None,
        audience=settings.JWT_AUDIENCE or None,
        options=options,
        leeway=_DEFAULT_LEEWAY_SECONDS,
    )

    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise ValueError("token missing/invalid sub")

    return payload
