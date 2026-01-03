# PR Title
`feat: production hardening layer (standard errors + global exception handling + optional rate limiting/cache/telemetry)`

## Description
This PR implements **Milestone 6: Production Hardening** for the reusable FastAPI template. It adds a clean, modular “hardening layer” that standardizes error responses across the API, provides global exception handling, and introduces **optional** performance/observability controls (rate limiting, Redis-backed cache, and telemetry hooks) without breaking any existing successful response schemas or routes.

Key non-negotiables preserved:
- `/health` still returns exactly `{"status":"ok"}`.
- `/auth/login` and `/api/v1/*` successful responses are unchanged.
- `X-Request-ID` tracing remains intact and is included in standardized error bodies.
- Docker + compose workflow remains intact.

## Changes

### Standard error response schema
- Added `backend/app/core/errors.py`:
  - `ErrorResponse` / `ErrorBody` (Pydantic models)
  - `error_response(...)` helper (returns `JSONResponse`)
  - `get_request_id()` which reuses the existing `contextvars` request-id mechanism
  - `code_for_http_status(...)` stable mapping (e.g., `validation_error`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `rate_limited`, `internal_error`)

All handled errors (via handlers below) return:

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

### Global exception handlers (standardized error bodies)
- Added `backend/app/core/exception_handlers.py` and registered in the app factory.
  - `RequestValidationError` → 422 `validation_error` with concise safe `details`
  - `HTTPException` (all status codes, including 404) → status-derived codes
    - Preserves important headers like `WWW-Authenticate` on 401
  - `Exception` → 500 `internal_error` (logs with stack trace; response does not leak internals)
  - Optional: SQLAlchemy `IntegrityError` → 409 `conflict` (safe generic response)

Logging policy:
- 4xx: INFO/WARNING (no stack traces)
- 5xx: ERROR with stack trace (request id included via logging filter)

### Rate limiting (optional, template-friendly)
- Added a small, pluggable rate limiting module:
  - `backend/app/core/rate_limit/interface.py` (RateLimiter protocol)
  - `backend/app/core/rate_limit/redis_backend.py` (Redis fixed-window using Lua for atomic INCR+EXPIRE)
  - `backend/app/core/rate_limit/middleware.py` (FastAPI/Starlette middleware)
  - `backend/app/core/rate_limit/__init__.py` (`build_rate_limiter(settings)`)

Behavior:
- Off by default (`RATE_LIMIT_ENABLED=false`).
- Applied to `/api/v1/*` **only** and excludes:
  - `/health`
  - `/api/v1/health/live`
  - `/api/v1/health/ready`
- Adds headers when enabled:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset` (epoch seconds)
- On exceeded: 429 with standardized error body (`error.code="rate_limited"`).
- Fail-open if Redis errors (guardrail should not become an availability risk).

### Cache backend (optional, Redis-backed)
- Added a small cache abstraction:
  - `backend/app/core/cache/interface.py`
  - `backend/app/core/cache/redis_cache.py`
  - `backend/app/core/cache/dependency.py` (`get_cache`)
  - `backend/app/core/cache/__init__.py` (`build_cache(settings)`)

Demo usage (safe, no schema change):
- Updated `backend/app/api/v1/routes/users.py`:
  - Caches `GET /api/v1/users/{id}` **after authorization** when enabled.
  - Caches only the `UserPublic` payload, never request-specific fields (e.g., request_id).
  - TTL strategy: `min(CACHE_DEFAULT_TTL_SECONDS, 60)` to keep user caching short-lived by default.
- Cache is fail-open if Redis is unavailable.

### Telemetry hooks (vendor-neutral)
- Added:
  - `backend/app/core/telemetry.py`:
    - `Telemetry` protocol
    - `NoopTelemetry` (default)
    - `LoggingTelemetry` (structured log metrics)
    - `build_telemetry(settings)`
  - `backend/app/core/telemetry_middleware.py`:
    - Emits `http_requests_total` and `http_request_duration_ms`
    - Tags include `method`, `status_code`, and route template when available
    - Optional sampling via `TELEMETRY_SAMPLE_RATE`

### App factory integration (hardening layer wiring)
- Updated `backend/app/core/app_factory.py`:
  - Registers exception handlers
  - Initializes `app.state.telemetry`, `app.state.cache`, `app.state.rate_limiter`
  - Adds middlewares (rate limit + telemetry + existing request-id + request logging)

### Settings + environment examples
- Updated `backend/app/core/config.py` with optional settings (off by default).
- Added `env.example` documenting the new vars (copy to `.env` for local compose usage).

### Docs
- Added `backend/docs/PROD_HARDENING.md` documenting:
  - error model + examples (401/403/404/409/422/429/500)
  - rate limiting enablement, keying strategy, headers, exemptions
  - cache enablement + TTL strategy + what is cached
  - telemetry modes and how to extend

### Tests (deterministic + hermetic)
Added test coverage for the new hardening layer:
- `backend/tests/test_prod_hardening_errors.py`
  - 404 under `/api/v1` returns standardized error schema with request_id
  - 422 validation error returns standardized schema and safe details
- `backend/tests/test_prod_hardening_rate_limit.py`
  - Disabled: no rate limit headers
  - Enabled: returns 429 and headers after exceeding limit (uses in-memory backend in test env)
- `backend/tests/test_prod_hardening_cache.py`
  - Cache enabled: confirms cached key is written and subsequent read works (uses in-memory backend in test env)
- `backend/tests/test_prod_hardening_telemetry.py`
  - Middleware calls the telemetry interface (fake telemetry)

## Milestone Completion Criteria
- [x] Consistent error behavior (standard schema + request_id)
- [x] Global exception handlers in place (422/HTTPException/500 + optional 409)
- [x] Optional rate limiting interface + Redis backend
- [x] Optional cache backend (Redis) with safe demonstration usage
- [x] Telemetry hooks with low-overhead defaults (noop/log)
- [x] Docs + tests added

## Notes / Design Decisions
- **Backwards compatibility**: success response schemas were not changed; only error responses were standardized via handlers.
- **Redis library consistency**: reused the existing pinned `redis` dependency for both rate limiting and cache.
- **Template safety**:
  - Rate limiting and cache are **off by default**.
  - When enabled but Redis is unavailable, both systems are **fail-open** to avoid outages.
- **Middleware organization**: telemetry middleware is kept separate from core request middleware to keep files small and responsibilities clear.

---

## Validation Commands for Reviewer
```bash
# 1) Local tooling
make fmt
make lint
make test
make precommit

# 2) Run stack (compose)
make up

# Legacy stays
curl -i http://localhost:8000/health
# expect: HTTP 200, {"status":"ok"}, X-Request-ID header present

# v1 health stays
curl -i http://localhost:8000/api/v1/health/live

# error schema check (expect standard error body)
curl -i http://localhost:8000/api/v1/does-not-exist

# Example: enable rate limiting (Redis required)
# RATE_LIMIT_ENABLED=true RATE_LIMIT_REQUESTS=2 RATE_LIMIT_WINDOW_SECONDS=60 make up
```

## End-to-end verification (with production tightening env enabled)

If your `.env` (or compose env) contains values like:

- `RATE_LIMIT_ENABLED=true`
- `CACHE_ENABLED=true`
- `TELEMETRY_MODE=log`

then you can validate the full hardening layer as follows.

### 0) Start the stack with your env file

```bash
make up
```

### 1) Verify dependencies are healthy (Postgres + Redis)

```bash
curl -i http://localhost:8000/api/v1/health/ready
# expect: HTTP 200 and body includes {"checks":{"db":"ok","redis":"ok"}}
```

### 2) Verify standard error schema + request_id (404)

```bash
curl -i http://localhost:8000/api/v1/does-not-exist
# expect: HTTP 404 with body:
# {"error":{"code":"not_found","message":"Not Found","request_id":"...","details":null}}
```

### 3) Verify rate limiting actually triggers 429 + headers

First confirm you get rate limit headers on a normal request:

```bash
curl -i http://localhost:8000/api/v1/does-not-exist
# expect headers:
# X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
```

Then send repeated requests until you hit 429:

```bash
python scripts/automated_tests/verify_prod_hardening.py http://localhost:8000
# expect: it prints "OK: prod hardening verification passed ..."
# and internally verifies a 429 response includes the standard error schema:
# {"error":{"code":"rate_limited",...}}
```

### 4) Verify cache is writing keys to Redis

The verifier script creates a user + logs in + calls `GET /api/v1/users/{id}` twice.
Then confirm the Redis key exists:

```bash
docker-compose exec -T redis redis-cli KEYS "cache:users:*"
# expect: at least one key like:
# cache:users:<uuid>
```

### 5) Verify telemetry is emitting metrics (log mode)

When `TELEMETRY_MODE=log`, requests emit structured log lines like:
- `metric.counter` (`http_requests_total`)
- `metric.histogram` (`http_request_duration_ms`)

```bash
docker-compose logs --tail=200 app
# expect to see lines containing "metric.counter" and "metric.histogram"
```

## Final logs analysis (what we observed in Docker)

With the “production tightening” env enabled (rate limiting + cache + telemetry log mode), we validated logs from the running stack and confirmed:

- **JSON logs are present**: the app emits one JSON object per log line when `LOG_JSON=true`.
- **request_id propagation works**: request logs and error/exception logs include `request_id` (from `X-Request-ID` / generated).
- **Telemetry is emitting**: logs contain `metric.counter` and `metric.histogram` events for requests.
- **Error responses correlate**: requests like `/api/v1/does-not-exist` show structured exception logs and return standardized error bodies (with the same request id).

### Export last N log lines into a clean JSON file (for review/sharing)

Docker log prefixes can make raw `docker-compose logs` output hard to parse as JSON. Use the helper script:

- `scripts/docker_logs/export_docker_logs_json.py`

Examples:

```bash
# Export last 200 lines of app logs as a single JSON document:
python scripts/docker_logs/export_docker_logs_json.py --compose-cmd "docker-compose" --service app --tail 200 --format array --out app-logs-200.json --dropped-out app-logs-200.dropped.txt

# Or as NDJSON (one JSON object per line):
python scripts/docker_logs/export_docker_logs_json.py --compose-cmd "docker-compose" --service app --tail 200 --format ndjson --out app-logs-200.ndjson --dropped-out app-logs-200.dropped.txt
```

What to expect:
- Output file contains:
  - `meta`: export metadata (tail size, parsed count, dropped count)
  - `records`: parsed JSON log objects (when `--format array`)
- It is normal to see some **dropped** lines if non-JSON lines are present (e.g., startup banners, non-app logs).


