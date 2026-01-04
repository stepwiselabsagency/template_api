# RATE LIMITING — `/api/v1/*` Guardrail

This template includes an optional, vendor-neutral rate limiting layer that is:

- **Off by default**
- **Scoped to `/api/v1/*` only**
- **Fail-open** (never blocks traffic if the limiter backend is unhealthy)

Implementation files:

- Middleware: `backend/app/core/rate_limit/middleware.py`
- Interface: `backend/app/core/rate_limit/interface.py`
- Redis backend: `backend/app/core/rate_limit/redis_backend.py`
- Builder/wiring: `backend/app/core/rate_limit/__init__.py` and `backend/app/core/app_factory.py`

Related docs:

- Error schema for 429 responses: `backend/docs/ERROR_MODEL.md`

---

## How to enable (env vars)

Required:

- `RATE_LIMIT_ENABLED=true`

Recommended (production-like):

- `REDIS_URL=redis://...`

Configuration:

- `RATE_LIMIT_REQUESTS` (default: `60`)
- `RATE_LIMIT_WINDOW_SECONDS` (default: `60`)
- `RATE_LIMIT_KEY_STRATEGY` (default: `ip`; allowed: `ip`, `user_or_ip`)
- `RATE_LIMIT_PREFIX` (default: `rl:`)

Where these live:

- `backend/app/core/config.py` (`Settings`)

---

## Scope rules (what is limited)

Truth from code (`backend/app/core/rate_limit/middleware.py`):

- **Included**: any path that starts with `/api/v1`
- **Excluded**:
  - `/health`
  - `/api/v1/health/live`
  - `/api/v1/health/ready`

This means:

- `GET /health` is never rate-limited.
- `GET /api/v1/users/me` can be rate-limited when enabled.

---

## Algorithm summary (fixed window + Redis atomicity)

Redis backend (`backend/app/core/rate_limit/redis_backend.py`) uses a **fixed-window counter**:

- Window start is computed as:
  - `window_start = now - (now % window_seconds)`
- A Redis key is incremented once per request in that window.
- Reset time returned is:
  - `reset = window_start + window_seconds` (epoch seconds)

Atomicity:

- Uses Redis **Lua** to perform `INCR` + `EXPIRE` atomically on first hit, avoiding race conditions under concurrency.

---

## Keying strategy (truthful to current implementation)

Key is built in two layers:

1) **Middleware** builds a logical key (no window suffix yet):

- Format: `"{RATE_LIMIT_PREFIX}{strategy}:{identifier}:global"`

2) **Redis backend** appends the window start:

- Final Redis key: `"{logical_key}:{window_start}"`

### `ip` strategy

Identifier is the client IP from `backend/app/core/rate_limit/middleware.py:_client_ip(...)`:

- If `X-Forwarded-For` is present: use the **first** comma-separated value.
- Else: use `request.client.host`.
- Fallback: `"unknown"`.

### `user_or_ip` strategy

- If `Authorization: Bearer <jwt>` is present and decodes successfully:
  - identifier is the JWT `sub` claim (string)
- Otherwise:
  - falls back to the `ip` strategy identifier

Note:

- This strategy does **not** consult the database; it is based on token decode only.

---

## Headers semantics

When rate limiting runs (even on blocked responses), the middleware attaches:

- `X-RateLimit-Limit`: configured limit (requests per window)
- `X-RateLimit-Remaining`: remaining requests in the current window (0 when blocked)
- `X-RateLimit-Reset`: epoch seconds when the current window resets

Where set:

- `backend/app/core/rate_limit/middleware.py` (after allow/block decision)

---

## Fail-open behavior (and rationale)

Rate limiting is designed as an **optional guardrail**. It fails open in these cases:

- `RATE_LIMIT_ENABLED=false` (default) → middleware bypasses
- Request path is out of scope or exempt → middleware bypasses
- `app.state.rate_limiter` is `None` → middleware bypasses
  - This happens if `RATE_LIMIT_ENABLED=true` but `REDIS_URL` is missing outside test (`backend/app/core/rate_limit/__init__.py`)
- Any exception while hitting the limiter backend → middleware logs and bypasses

Rationale:

- Availability-first: the limiter must not take down the API if Redis is degraded.

---

## Local testing instructions

### With Redis (recommended)

1) Ensure `.env` contains `REDIS_URL` (Compose already exposes Redis on `localhost:6379` by default).
2) Set rate limiting vars in `.env`:

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=2
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_KEY_STRATEGY=ip
```

3) Restart:

```bash
make down
make up
```

4) Hit a v1 endpoint repeatedly:

```bash
curl -i http://localhost:8000/api/v1/users/me
```

Expect 401 (no auth) until you exceed the limit, then 429 with the standard error schema.

### Without Redis (what happens)

- In `ENV=test`, the builder returns an in-memory limiter.
- Outside `test`, if `REDIS_URL` is not set, the limiter is **disabled** and requests are not rate-limited (fail-open).

Where this is decided:

- `backend/app/core/rate_limit/__init__.py:build_rate_limiter(...)`

---

## How to swap the implementation

Interface:

- `backend/app/core/rate_limit/interface.py` defines the `RateLimiter` protocol:
  - `hit(key, limit, window_seconds) -> (allowed, remaining, reset_epoch_seconds)`

To swap:

- Add a new implementation (example file): `backend/app/core/rate_limit/<your_backend>.py`
- Update `build_rate_limiter(...)` in `backend/app/core/rate_limit/__init__.py` to return it

Do not change:

- Middleware scope rules (unless you also update the public documentation).
- Header semantics.
- Error schema for 429 responses (`backend/docs/ERROR_MODEL.md`).


