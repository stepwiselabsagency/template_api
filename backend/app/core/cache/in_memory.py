from __future__ import annotations

import time

from app.core.cache.interface import Cache


class InMemoryCache(Cache):
    """
    Minimal in-memory cache for tests/local usage when Redis is not configured.
    Not suitable for multi-process deployments.
    """

    def __init__(self, *, prefix: str = "cache:") -> None:
        self._prefix = prefix
        self._data: dict[str, tuple[str, float | None]] = {}

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> str | None:
        k = self._k(key)
        item = self._data.get(k)
        if not item:
            return None
        value, expires_at = item
        if expires_at is not None and time.time() > expires_at:
            self._data.pop(k, None)
            return None
        return value

    def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        expires_at = None
        if ttl_seconds is not None:
            expires_at = time.time() + int(ttl_seconds)
        self._data[self._k(key)] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._data.pop(self._k(key), None)
