from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from app.core.config import Settings

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: str | None) -> Any:
    """
    Set request_id into contextvars for the current request/task.

    Returns a token that can be used with `reset_request_id(...)`.
    """
    return _request_id_ctx.set(request_id)


def reset_request_id(token: Any) -> None:
    _request_id_ctx.reset(token)


def get_request_id() -> str | None:
    return _request_id_ctx.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": getattr(record, "request_id", None),
        }

        # Optional structured fields (middleware can pass these via `extra=...`)
        for key in ("path", "method", "status_code", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def _configure_root_logger(level: str, handler: logging.Handler) -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Replace any existing handlers to keep output predictable
    # (especially under Uvicorn).
    root.handlers = [handler]
    root.propagate = False


def configure_logging(settings: Settings) -> None:
    """
    Configure root logging once during app creation.
    """
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.addFilter(RequestIdFilter())

    if settings.LOG_JSON:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt=(
                    "%(asctime)s %(levelname)s %(name)s "
                    "request_id=%(request_id)s %(message)s"
                )
            )
        )

    _configure_root_logger(settings.LOG_LEVEL, handler)

    logging.getLogger(__name__).info("logging configured")
