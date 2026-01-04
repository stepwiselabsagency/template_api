# Production Hardening (Template Features)

This template ships with **production-hardening hooks** that are:

- **Safe by default**
- **Vendor-neutral**
- **Mostly optional** (toggled by environment variables)

This doc is the **overview**. Source-of-truth details live in the linked docs below.

## Docs index (source of truth)

- **Architecture / wiring**: `backend/docs/ARCHITECTURE.md`
- **Error model (client contract)**: `backend/docs/ERROR_MODEL.md`
- **Rate limiting**: `backend/docs/RATE_LIMITING.md`
- **Auth model**: `backend/docs/AUTH_MODEL.md`

## Where it’s wired

- App factory: `backend/app/core/app_factory.py`
- Exception handlers: `backend/app/core/exception_handlers.py`
- Request id + request logging: `backend/app/core/middleware.py`
- Logging setup + request id context: `backend/app/core/logging.py`

## Cache (Optional; Redis-backed)

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


