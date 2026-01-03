from __future__ import annotations

import time
from collections import defaultdict

from app.core.rate_limit.interface import RateLimiter


class InMemoryRateLimiter(RateLimiter):
    """
    Best-effort in-memory limiter.

    Intended for tests/local usage when Redis is not configured.
    Not suitable for multi-process deployments.
    """

    def __init__(self) -> None:
        self._counts: defaultdict[str, int] = defaultdict(int)

    def hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        now = int(time.time())
        window_start = now - (now % int(window_seconds))
        reset = window_start + int(window_seconds)

        window_key = f"{key}:{window_start}"
        self._counts[window_key] += 1
        current = self._counts[window_key]

        allowed = current <= int(limit)
        remaining = max(0, int(limit) - current)
        return allowed, remaining, reset
