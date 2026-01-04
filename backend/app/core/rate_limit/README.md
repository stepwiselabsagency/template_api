# `backend/app/core/rate_limit/` — Rate limiting (optional)

## Purpose

- Provides an optional rate limiting layer with a small interface and a default Redis implementation.

## Key modules/files

- **Interface**: `backend/app/core/rate_limit/interface.py` (`RateLimiter`)
- **Middleware** (scope + headers + fail-open): `backend/app/core/rate_limit/middleware.py`
- **Backends**:
  - `backend/app/core/rate_limit/redis_backend.py` (fixed window + Lua atomicity)
  - `backend/app/core/rate_limit/in_memory.py` (tests)
- **Builder**: `backend/app/core/rate_limit/__init__.py` (`build_rate_limiter`)

## How it connects

- `backend/app/core/app_factory.py` sets `app.state.rate_limiter = build_rate_limiter(settings)`
- `RateLimitMiddleware` reads `request.app.state.rate_limiter` and enforces limits for `/api/v1/*`

## Extension points

- Swap backend: implement `RateLimiter.hit(...)` and update `build_rate_limiter(...)`.
- Change scope/exemptions: edit `_should_rate_limit(...)` and `_EXEMPT_PATHS` in `backend/app/core/rate_limit/middleware.py` (and update docs).

## Pitfalls / invariants

- Scope is intentionally limited to `/api/v1/*` with health exemptions.
- Rate limiting must **fail open** on backend errors (availability-first guardrail).

## Related docs

- `backend/docs/RATE_LIMITING.md`
- `backend/docs/ERROR_MODEL.md` (429 response envelope)


