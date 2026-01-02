from __future__ import annotations

import hashlib


def hash_password(password: str) -> str:
    """
    Placeholder password hashing.

    IMPORTANT: This is NOT production-grade. It exists only to prove end-to-end
    persistence wiring in this template milestone. Replace with a proper
    password hashing scheme (e.g., passlib/bcrypt/argon2) before production use.
    """

    if password is None:
        raise ValueError("password must not be None")
    return hashlib.sha256(password.encode("utf-8")).hexdigest()
