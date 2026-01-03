from __future__ import annotations

from app.core.cache.interface import Cache
from app.core.cache.noop import NoopCache
from starlette.requests import Request


def get_cache(request: Request) -> Cache:
    cache = getattr(request.app.state, "cache", None)  # type: ignore[attr-defined]
    if cache is None:
        return NoopCache()
    return cache
