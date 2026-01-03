from __future__ import annotations

import logging
from typing import Any

from app.core.errors import code_for_http_status, error_response, get_request_id
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp

try:
    # Optional handler for DB uniqueness, etc.
    from sqlalchemy.exc import IntegrityError  # type: ignore
except Exception:  # pragma: no cover
    IntegrityError = None  # type: ignore


log = logging.getLogger("app.exceptions")


def _safe_validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for err in exc.errors():
        details.append(
            {
                "loc": list(err.get("loc") or []),
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
        )
    return details


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
):
    request_id = get_request_id()
    log.warning(
        "validation error",
        extra={"path": request.url.path, "method": request.method, "status_code": 422},
    )
    return error_response(
        code="validation_error",
        message="Validation error",
        request_id=request_id,
        status_code=422,
        details=_safe_validation_details(exc),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = get_request_id()
    status_code = int(getattr(exc, "status_code", 500) or 500)
    code = code_for_http_status(status_code)
    headers = getattr(exc, "headers", None)

    # FastAPI/Starlette `detail` can be str | dict | list; keep safe by returning
    # only string messages to clients.
    raw_detail = getattr(exc, "detail", None)
    message = raw_detail if isinstance(raw_detail, str) and raw_detail else "HTTP error"

    if 500 <= status_code:
        log.exception(
            "http exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
            },
        )
    elif status_code in {401, 403}:
        log.warning(
            "http exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
            },
        )
    else:
        log.info(
            "http exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
            },
        )

    return error_response(
        code=code,
        message=message,
        request_id=request_id,
        status_code=status_code,
        details=None,
        headers=headers,
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = get_request_id()
    log.exception(
        "unhandled exception",
        extra={"path": request.url.path, "method": request.method, "status_code": 500},
    )
    return error_response(
        code="internal_error",
        message="Internal server error",
        request_id=request_id,
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def integrity_error_handler(request: Request, exc: Exception):
    # Keep response safe and generic; do not leak constraint names.
    request_id = get_request_id()
    log.warning(
        "integrity error",
        extra={"path": request.url.path, "method": request.method, "status_code": 409},
    )
    return error_response(
        code="conflict",
        message="Conflict",
        request_id=request_id,
        status_code=409,
        details=None,
    )


def register_exception_handlers(app: ASGIApp) -> None:
    """
    Register global exception handlers to standardize error responses.
    """

    # FastAPI wraps validation issues into this exception class.
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)  # type: ignore[attr-defined]
    # Starlette/FastAPI HTTPException (includes 404).
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[attr-defined]
    # DB integrity errors -> 409 conflict when SQLAlchemy is in use.
    if IntegrityError is not None:  # pragma: no cover
        app.add_exception_handler(IntegrityError, integrity_error_handler)  # type: ignore[arg-type,attr-defined]
    # Catch-all.
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[attr-defined]
