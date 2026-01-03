from __future__ import annotations

import time

import redis
from app.core.rate_limit.interface import RateLimiter

_HIT_LUA = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""


class RedisRateLimiter(RateLimiter):
    """
    Fixed-window rate limiter using Redis INCR + EXPIRE via Lua for atomicity.
    """

    def __init__(self, redis_url: str, *, socket_timeout: float = 1.0) -> None:
        self._client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=socket_timeout,
            socket_timeout=socket_timeout,
        )
        self._hit = self._client.register_script(_HIT_LUA)

    def hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        now = int(time.time())
        window_start = now - (now % int(window_seconds))
        reset = window_start + int(window_seconds)

        window_key = f"{key}:{window_start}"
        current = int(self._hit(keys=[window_key], args=[int(window_seconds)]))

        allowed = current <= int(limit)
        remaining = max(0, int(limit) - current)
        return allowed, remaining, reset
