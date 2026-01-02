from __future__ import annotations

from passlib.context import CryptContext
from passlib.exc import UnknownHashError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    if plain is None:
        raise ValueError("plain password must not be None")
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    if plain is None or hashed is None:
        return False
    # passlib handles constant-time verification and algorithm upgrades.
    # If the stored hash is from an unknown/legacy scheme, treat it as invalid
    # (don't crash the request path).
    try:
        return _pwd_context.verify(plain, hashed)
    except (UnknownHashError, ValueError, TypeError):
        return False
