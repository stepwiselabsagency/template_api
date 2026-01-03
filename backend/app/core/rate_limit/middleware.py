from __future__ import annotations

import logging
from typing import Callable

import anyio
from app.auth.jwt import decode_token
from app.core.config import Settings
from app.core.errors import error_response, get_request_id
from app.core.rate_limit.interface import RateLimiter
from app.core.rate_limit.redis_backend import RedisRateLimiter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = logging.getLogger("app.rate_limit")

_EXEMPT_PATHS = {
    "/health",
    "/api/v1/health/live",
    "/api/v1/health/ready",
}


def _client_ip(request: Request) -> str:
    # Best-effort: support proxies via first X-Forwarded-For value.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _user_id_from_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        payload = decode_token(token)
    except Exception:
        return None
    sub = payload.get("sub")
    if isinstance(sub, str) and sub:
        return sub
    return None


def _should_rate_limit(path: str) -> bool:
    if path in _EXEMPT_PATHS:
        return False
    return path.startswith("/api/v1")


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Callable,
        *,
        settings: Settings,
    ) -> None:
        super().__init__(app)
        self._enabled = bool(settings.RATE_LIMIT_ENABLED)
        self._limit = int(settings.RATE_LIMIT_REQUESTS)
        self._window = int(settings.RATE_LIMIT_WINDOW_SECONDS)
        self._prefix = settings.RATE_LIMIT_PREFIX or "rl:"
        self._strategy = (settings.RATE_LIMIT_KEY_STRATEGY or "ip").strip().lower()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self._enabled or not _should_rate_limit(request.url.path):
            return await call_next(request)

        limiter: RateLimiter | None = getattr(request.app.state, "rate_limiter", None)  # type: ignore[attr-defined]
        if limiter is None:
            return await call_next(request)

        identifier: str | None = None
        strategy = self._strategy
        if strategy == "user_or_ip":
            identifier = _user_id_from_bearer_token(request) or _client_ip(request)
        else:
            strategy = "ip"
            identifier = _client_ip(request)

        key = f"{self._prefix}{strategy}:{identifier}:global"

        try:
            if isinstance(limiter, RedisRateLimiter):
                allowed, remaining, reset = await anyio.to_thread.run_sync(
                    limiter.hit, key, self._limit, self._window
                )
            else:
                allowed, remaining, reset = limiter.hit(key, self._limit, self._window)
        except Exception:
            # Fail open for safety; rate limiting is an optional guardrail.
            log.exception(
                "rate limiter error (fail-open)",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": 200,
                },
            )
            return await call_next(request)

        if allowed:
            response = await call_next(request)
        else:
            request_id = get_request_id()
            response = error_response(
                code="rate_limited",
                message="Too many requests",
                request_id=request_id,
                status_code=429,
                details=None,
            )

        response.headers["X-RateLimit-Limit"] = str(self._limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)
        return response
