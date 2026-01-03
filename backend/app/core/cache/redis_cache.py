from __future__ import annotations

import logging

import redis
from app.core.cache.interface import Cache

log = logging.getLogger("app.cache")


class RedisCache(Cache):
    def __init__(
        self,
        redis_url: str,
        *,
        prefix: str = "cache:",
        socket_timeout: float = 1.0,
    ) -> None:
        self._prefix = prefix
        self._client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=socket_timeout,
            socket_timeout=socket_timeout,
        )

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> str | None:
        try:
            val = self._client.get(self._k(key))
        except Exception:
            log.exception("cache get failed (fail-open)")
            return None
        if val is None:
            return None
        if isinstance(val, bytes):
            return val.decode("utf-8", errors="replace")
        return str(val)

    def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        try:
            if ttl_seconds is None:
                self._client.set(self._k(key), value)
            else:
                self._client.setex(self._k(key), int(ttl_seconds), value)
        except Exception:
            log.exception("cache set failed (fail-open)")

    def delete(self, key: str) -> None:
        try:
            self._client.delete(self._k(key))
        except Exception:
            log.exception("cache delete failed (fail-open)")
