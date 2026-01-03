from __future__ import annotations

import random
import time
from typing import Callable

from app.core.config import Settings
from app.core.telemetry import Telemetry
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path_format = getattr(route, "path_format", None)
    if isinstance(path_format, str) and path_format:
        return path_format
    return request.url.path


class TelemetryMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Callable, *, settings: Settings) -> None:
        super().__init__(app)
        self._sample_rate = float(settings.TELEMETRY_SAMPLE_RATE)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        sample = self._sample_rate >= 1.0 or random.random() < self._sample_rate
        if not sample:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        telemetry: Telemetry = request.app.state.telemetry  # type: ignore[attr-defined]
        tags = {
            "method": request.method,
            "path": _route_template(request),
            "status_code": str(response.status_code),
        }
        telemetry.incr_counter("http_requests_total", 1, tags=tags)
        telemetry.observe_histogram(
            "http_request_duration_ms", float(round(duration_ms, 2)), tags=tags
        )
        return response
