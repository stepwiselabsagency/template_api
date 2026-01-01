from __future__ import annotations

import logging
import time
from typing import Callable
from uuid import uuid4

from app.core.config import Settings
from app.core.logging import reset_request_id, set_request_id
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.request")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Ensure every request has a request_id:
    - read from configured header if present
    - otherwise generate a uuid4
    - store in contextvars for downstream logging
    - attach to response headers
    """

    def __init__(self, app: Callable, *, settings: Settings) -> None:
        super().__init__(app)
        self._header = settings.REQUEST_ID_HEADER

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming = request.headers.get(self._header)
        request_id = incoming or str(uuid4())

        token = set_request_id(request_id)
        try:
            response = await call_next(request)
        finally:
            reset_request_id(token)

        response.headers[self._header] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log a single summary line per request (and exceptions) with request context.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request complete",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        return response
