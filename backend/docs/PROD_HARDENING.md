# Production Hardening (Template Features)

This template ships with **production hardening hooks** that are **safe by default** and **optional/configurable** via environment variables.

## Error Model (Standard Error Response)

All errors handled by the global exception handlers return:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "request_id": "string",
    "details": { "any": "json" }
  }
}
```

- **Code**: stable machine-readable (`validation_error`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `rate_limited`, `internal_error`, etc.)
- **Message**: safe human-readable string (no secrets)
- **Request id**: derived from `X-Request-ID` via `contextvars` (`app/core/logging.py`)
- **Details**: optional safe structured context (e.g., validation fields)

### Where it lives

- `backend/app/core/errors.py`
  - `ErrorResponse` / `ErrorBody`
  - `error_response(...)`
  - `get_request_id()`

### Examples

- **404** (`GET /api/v1/does-not-exist`)

```json
{
  "error": {
    "code": "not_found",
    "message": "Not Found",
    "request_id": "…",
    "details": null
  }
}
```

- **422** (validation error)

```json
{
  "error": {
    "code": "validation_error",
    "message": "Validation error",
    "request_id": "…",
    "details": [
      {"loc": ["body", "password"], "msg": "Field required", "type": "missing"}
    ]
  }
}
```

- **500** (unhandled exception)

```json
{
  "error": {
    "code": "internal_error",
    "message": "Internal server error",
    "request_id": "…",
    "details": null
  }
}
```

## Global Exception Handling

Registered in `backend/app/core/app_factory.py` via:

- `backend/app/core/exception_handlers.py`
  - `register_exception_handlers(app)`

Handlers:

- `RequestValidationError` → 422 `validation_error`
- `HTTPException` (including 404) → status-derived codes
- `IntegrityError` (SQLAlchemy; optional) → 409 `conflict`
- `Exception` → 500 `internal_error`

Logging policy:

- 4xx: INFO/WARNING (no stack traces)
- 5xx: ERROR with stack trace and request id (via logging filter)

## Rate Limiting (Optional)

### Enable

Set:

- `RATE_LIMIT_ENABLED=true`
- `REDIS_URL=redis://…` (required outside tests)

Config:

- `RATE_LIMIT_REQUESTS` (default: 60)
- `RATE_LIMIT_WINDOW_SECONDS` (default: 60)
- `RATE_LIMIT_KEY_STRATEGY` (`ip` or `user_or_ip`)
- `RATE_LIMIT_PREFIX` (default: `rl:`)

### Scope + Exemptions

Applied to:

- `/api/v1/*`

Not applied to:

- `/health`
- `/api/v1/health/live`
- `/api/v1/health/ready`

### Headers

When enabled, responses include:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset` (epoch seconds)

### Behavior

On limit exceeded: 429 with:

- `error.code="rate_limited"`
- `error.message="Too many requests"`

### Implementation

- `backend/app/core/rate_limit/interface.py` – `RateLimiter`
- `backend/app/core/rate_limit/redis_backend.py` – Redis fixed window (Lua atomic)
- `backend/app/core/rate_limit/middleware.py` – `/api/v1` middleware

Keying:

- `ip`: uses `X-Forwarded-For` first hop if present, otherwise `request.client.host`
- `user_or_ip`: attempts to decode Bearer JWT and uses `sub` if present, else falls back to IP

## Cache (Optional; Redis-backed)

### Enable

- `CACHE_ENABLED=true`
- `REDIS_URL=redis://…`

Config:

- `CACHE_DEFAULT_TTL_SECONDS` (default: 300)
- `CACHE_PREFIX` (default: `cache:`)

### What is cached

Demo caching is applied to:

- `GET /api/v1/users/{id}` (only after authorization)

TTL strategy:

- Uses `min(CACHE_DEFAULT_TTL_SECONDS, 60)` to keep cached user data short-lived by default.

Important:

- Only the `UserPublic` payload is cached.
- Request-specific data like `request_id` is **never cached**.

### Implementation

- `backend/app/core/cache/interface.py`
- `backend/app/core/cache/redis_cache.py`
- `backend/app/core/cache/dependency.py` (`get_cache`)
- `backend/app/api/v1/routes/users.py` uses `get_cache`

## Telemetry Hooks (Optional; vendor-neutral)

Default is no-op.

### Enable structured log metrics

- `TELEMETRY_MODE=log`

Config:

- `TELEMETRY_SAMPLE_RATE` (default: 1.0)

### Signals

Middleware emits:

- counter: `http_requests_total`
- histogram: `http_request_duration_ms`

Tags:

- `method`
- `path` (prefers route template when available)
- `status_code`

Implementation:

- `backend/app/core/telemetry.py` (`Telemetry`, `NoopTelemetry`, `LoggingTelemetry`)
- `backend/app/core/telemetry_middleware.py`

## How to extend (template-friendly)

- Swap telemetry:
  - Implement the `Telemetry` protocol in `backend/app/core/telemetry.py`
  - Update `build_telemetry(settings)` to return your backend client
- Swap rate limiter backend:
  - Implement `RateLimiter.hit(...)`
  - Update `build_rate_limiter(settings)` in `backend/app/core/rate_limit/__init__.py`
- Add cache invalidation:
  - Add `cache.delete("users:<id>")` in user update/delete routes (if your project adds them)


