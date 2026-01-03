from __future__ import annotations

from app.core.cache.interface import Cache


class NoopCache(Cache):
    def get(self, key: str) -> str | None:
        return None

    def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        return None

    def delete(self, key: str) -> None:
        return None
