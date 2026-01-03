from __future__ import annotations

import logging

from app.core.config import Settings
from app.core.rate_limit.in_memory import InMemoryRateLimiter
from app.core.rate_limit.interface import RateLimiter
from app.core.rate_limit.redis_backend import RedisRateLimiter

log = logging.getLogger(__name__)


def build_rate_limiter(settings: Settings) -> RateLimiter | None:
    if not settings.RATE_LIMIT_ENABLED:
        return None

    if settings.REDIS_URL:
        return RedisRateLimiter(settings.REDIS_URL)

    # Redis is the intended backend, but keep the template test-friendly.
    if settings.ENV == "test":
        return InMemoryRateLimiter()

    log.warning("RATE_LIMIT_ENABLED=true but REDIS_URL is not configured; disabling")
    return None
