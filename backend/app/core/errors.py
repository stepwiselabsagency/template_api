from __future__ import annotations

from typing import Any

from app.core.logging import get_request_id as _get_request_id
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str | None = None
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


def get_request_id() -> str | None:
    """
    Reuse the existing request id context mechanism (contextvars).
    """

    return _get_request_id()


def error_response(
    *,
    code: str,
    message: str,
    request_id: str | None,
    status_code: int,
    details: Any | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            request_id=request_id,
            details=details,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
        headers=headers,
    )


def code_for_http_status(status_code: int) -> str:
    """
    Stable machine-readable error code mapping.
    """

    if status_code == 400:
        return "bad_request"
    if status_code == 401:
        return "unauthorized"
    if status_code == 403:
        return "forbidden"
    if status_code == 404:
        return "not_found"
    if status_code == 409:
        return "conflict"
    if status_code == 422:
        return "validation_error"
    if status_code == 429:
        return "rate_limited"
    if status_code >= 500:
        return "internal_error"
    return "http_error"
