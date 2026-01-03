from __future__ import annotations

import logging

from app.core.cache.in_memory import InMemoryCache
from app.core.cache.interface import Cache
from app.core.cache.noop import NoopCache
from app.core.cache.redis_cache import RedisCache
from app.core.config import Settings

log = logging.getLogger(__name__)


def build_cache(settings: Settings) -> Cache:
    if not settings.CACHE_ENABLED:
        return NoopCache()

    if settings.REDIS_URL:
        return RedisCache(
            settings.REDIS_URL,
            prefix=settings.CACHE_PREFIX or "cache:",
        )

    if settings.ENV == "test":
        return InMemoryCache(prefix=settings.CACHE_PREFIX or "cache:")

    log.warning("CACHE_ENABLED=true but REDIS_URL is not configured; using NoopCache")
    return NoopCache()
