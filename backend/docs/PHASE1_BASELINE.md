# PHASE 01 BASELINE — Locked Truth (Phase 01 only)

This document is the **baseline truth** of Phase 01 for this repository. It is intentionally explicit and file-path driven so Phase 02 restructuring can proceed safely with **no runtime behavior changes**.

Important:
- This is a **Phase 01 snapshot**. In Phase 02, the canonical public API surface is `/api/v1/*` and duplicate legacy routes may be removed.
- For the current canonical API surface, see: `backend/app/api/v1/README.md` and `backend/docs/ONBOARDING.md`.

Scope rules:
- **In scope**: current behavior as implemented in code/tests/docs in this repo.
- **Out of scope**: Phase 02 planning, refactors, or “should” statements.

---

## 1) Purpose and scope

- **Purpose**: Provide a stable reference for what Phase 01 ships: entrypoints, endpoints, invariants, configuration, scripts, and test/CI facts.
- **Scope**: The FastAPI service under `backend/` plus repo tooling (`Makefile`, `docker-compose.yml`, `scripts/`).

---

## 2) System overview

This repository is a **FastAPI backend template** with:
- **FastAPI app**: created by `backend/app/core/app_factory.py:create_app()` and exported as `app` in `backend/app/main.py`.
- **Database layer**: SQLAlchemy + Alembic migrations (`backend/app/db/`, `backend/alembic/`).
- **Postgres + Redis local stack**: via `docker-compose.yml` (services: `postgres`, `redis`, `app`).
- Optional “hardening hooks” (implemented, toggled by env):
  - Request id correlation (`backend/app/core/middleware.py`)
  - Standard error envelope (`backend/app/core/exception_handlers.py`, `backend/app/core/errors.py`)
  - Rate limiting (`backend/app/core/rate_limit/` + middleware)
  - Cache (`backend/app/core/cache/`)
  - Telemetry hooks (`backend/app/core/telemetry.py` + middleware)

---

## 3) Runtime entrypoint and local stack

### Uvicorn / ASGI entrypoint (truth from code)

- **ASGI app export**: `backend/app/main.py` exports `app`:
  - `from app.core.app_factory import create_app`
  - `app = create_app()`
- **Docker runtime command**: `Dockerfile` runs:
  - `uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8000}`

### Docker Compose stack (truth from `docker-compose.yml`)

Services:
- **`postgres`**
  - image: `postgres:16.3-alpine`
  - port mapping: `${POSTGRES_PORT:-5432}:5432`
  - env: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- **`redis`**
  - image: `redis:7.2.5-alpine`
  - port mapping: `6379:6379`
- **`app`**
  - built from `Dockerfile` at repo root
  - exposes `8000:8000`
  - depends on `postgres` and `redis` healthchecks
  - environment includes `APP_ENV`, `APP_PORT`, `DATABASE_URL`, `REDIS_URL` (see `docker-compose.yml`)

---

## 4) Public endpoints (complete list)

Routing truth:
- Root health is defined directly in `backend/app/core/app_factory.py` at `GET /health`.
- Versioned API router is `backend/app/api/v1/router.py` mounted at `/api/v1` in `backend/app/core/app_factory.py`.

All endpoints below include **response header `X-Request-ID`** (default header name) due to `backend/app/core/middleware.py:RequestIdMiddleware`.

### Health (root)

- **GET `/health`**
  - **Auth**: no
  - **Success**: `200`
  - **Response body**: `{"status":"ok"}`
    - Contract is asserted in:
      - `backend/tests/test_health.py`
      - `scripts/automated_tests/verify_prod_hardening.py` (expects exact JSON bytes: `{"status":"ok"}`)
  - **Dependencies**: does not require DB/Redis

### Health (v1)

Mounted under `/api/v1` via `backend/app/api/v1/router.py`.

- **GET `/api/v1/health/live`**
  - **Auth**: no
  - **Success**: `200`
  - **Response body**: `{"status":"ok"}`
  - **Dependencies**: does not require DB/Redis (pure liveness)

- **GET `/api/v1/health/ready`**
  - **Auth**: no
  - **Success**: `200` when ready; `503` when not ready
  - **Response body (ready, 200)**:
    - `{"status":"ok","checks":{"db":"ok","redis":"ok"}}`
  - **Response body (not ready, 503)**:
    - `{"status":"error","checks":{"db":"error|ok","redis":"error|ok"}}`
  - **Readiness rules (truth from `backend/app/api/v1/routes/health.py` + tests)**:
    - **DB**:
      - If `settings.DATABASE_URL` is empty → readiness fails (`db="error"`, status `503`)
      - If `DATABASE_URL` is configured and connectable → `db="ok"`
    - **Redis**:
      - If `settings.REDIS_URL` is empty → treated as **ok** (readiness can still pass)
      - If `REDIS_URL` is configured but unreachable → readiness fails (`redis="error"`, status `503`)

### Auth (v1)

Mounted from `backend/app/api/v1/routes/auth.py` under `/api/v1/auth`.

- **POST `/api/v1/auth/login`**
  - **Auth**: no
  - **Request**: `application/x-www-form-urlencoded` (`OAuth2PasswordRequestForm`)
    - fields: `username` (treated as email), `password`
  - **Success**: `200`
  - **Response body shape**:
    - `{"access_token":"<jwt>","token_type":"bearer","expires_in":<int>}`
  - **Notes (truth from `backend/app/auth/dependencies.py`)**:
    - Protected routes use `OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`

- **GET `/api/v1/auth/me`**
  - **Auth**: yes (Bearer token; `get_current_user`)
  - **Success**: `200`
  - **Response body shape**:
    - `{"id":"<uuid>","email":"<str>","is_active":<bool>,"is_superuser":<bool>}`

### Users (v1)

Mounted from `backend/app/api/v1/routes/users.py` under `/api/v1/users`.

- **POST `/api/v1/users`**
  - **Auth**: no
  - **Success**: `201`
  - **Request body shape**: `{"email":"<str>","password":"<str>"}`
  - **Response body shape**:
    - `{"id":"<uuid>","email":"<str>","is_active":<bool>,"is_superuser":<bool>}`

- **GET `/api/v1/users/me`**
  - **Auth**: yes
  - **Success**: `200`
  - **Response body shape**: `UserPublic` (same fields as create response)

- **GET `/api/v1/users/{user_id}`**
  - **Auth**: yes
  - **Success**: `200`
  - **Authorization rule (truth from code)**:
    - Allowed if `current_user.id == user_id` OR `current_user.is_superuser == True`
    - Otherwise: `403` with `detail="Not enough permissions"` (handled by standard error envelope)
  - **Caching behavior (conditional)**:
    - Only when `CACHE_ENABLED=true` (see config section)
    - Cache key: `users:{user_id}`
    - Stored value: JSON of `UserPublic`
    - TTL: `min(CACHE_DEFAULT_TTL_SECONDS, 60)`

---

## 5) Contractual invariants

### `/health` exact response

Contract: `GET /health` must return JSON body exactly:

- `{"status":"ok"}`

This is asserted in:
- `backend/tests/test_health.py` (JSON object equality + header existence)
- `scripts/automated_tests/verify_prod_hardening.py` (exact `body.strip() == '{"status":"ok"}'`)

### Request id behavior (`X-Request-ID`)

Truth from `backend/app/core/middleware.py:RequestIdMiddleware`:
- Incoming header name is configurable via `Settings.REQUEST_ID_HEADER` (default: `X-Request-ID`).
- If the incoming request includes that header, the same value is **echoed** back in the response.
- Otherwise, a new UUID4 string is generated and returned as the response header.
- The request id is also stored in contextvars for logging via `backend/app/core/logging.py`.

### Standardized error envelope

Truth from `backend/app/core/exception_handlers.py` + `backend/app/core/errors.py`:
- Handled errors are returned as:

```json
{"error":{"code":"string","message":"string","request_id":"string|null","details":"any|null"}}
```

Where it applies:
- Registered globally in `backend/app/core/app_factory.py:register_exception_handlers(app)` (before routers are mounted), so it applies across routes (including `/api/v1`).

Required observed behaviors under `/api/v1` (verified by integration tests):
- `GET /api/v1/does-not-exist` → `404` with `{"error": ...}` and `error.request_id` equals response `X-Request-ID` (`backend/tests/integration/test_api_integration.py`).
- `POST /api/v1/users` with missing fields → `422` with `{"error": ...}` including `error.request_id` (`backend/tests/integration/test_api_integration.py`).

---

## 6) Configuration and environment variables

Primary settings are defined in `backend/app/core/config.py:Settings` and loaded from environment variables (and `.env` in local dev).

### Core app
- **`APP_ENV` / `ENV`**: defaults to `local` (alias supported: `APP_ENV`), tests force `APP_ENV=test` (see tests section)
- **`DEBUG`**: default `false`
- **`APP_NAME`**: default `backend`
- **`API_PREFIX`**: default empty string; used as prefix for legacy router mount (`backend/app/core/app_factory.py`)

### Logging / request id
- **`LOG_LEVEL`**: default `INFO`
- **`LOG_JSON`**: default `true`
- **`REQUEST_ID_HEADER`**: default `X-Request-ID`

### Database / Redis
Truth from `backend/app/core/config.py` + `backend/app/db/session.py`:
- **`DATABASE_URL`**
  - default: empty string (tests/local can run without DB unless a test opts in)
  - required for any endpoint that uses `get_db` (DB session dependency raises if not configured)
  - readiness endpoint treats empty `DATABASE_URL` as not ready (503)
- **`REDIS_URL`**
  - default: empty string
  - optional; readiness treats empty as ok

### CORS
- **`CORS_ALLOW_ORIGINS`**: list of origins; when non-empty, enables `CORSMiddleware` in `backend/app/core/app_factory.py`

### Auth / JWT
- **`JWT_SECRET_KEY`**
  - default: `CHANGE_ME_IN_PROD`
  - **required outside** `APP_ENV in {"local","test"}` (validator enforces this in `backend/app/core/config.py`)
- **`JWT_ALGORITHM`**: default `HS256`
- **`JWT_ACCESS_TOKEN_EXPIRES_MINUTES`**: default `60`
- **`JWT_ISSUER`**: optional (empty default)
- **`JWT_AUDIENCE`**: optional (empty default)

### Production hardening toggles (optional by config)
Truth from `backend/app/core/config.py` and middleware wiring in `backend/app/core/app_factory.py`:
- **Rate limiting**
  - `RATE_LIMIT_ENABLED` (default false)
  - `RATE_LIMIT_REQUESTS` (default 60)
  - `RATE_LIMIT_WINDOW_SECONDS` (default 60)
  - `RATE_LIMIT_KEY_STRATEGY` (default `ip`, allowed `ip|user_or_ip`)
  - `RATE_LIMIT_PREFIX` (default `rl:`)
- **Cache**
  - `CACHE_ENABLED` (default false)
  - `CACHE_DEFAULT_TTL_SECONDS` (default 300)
  - `CACHE_PREFIX` (default `cache:`)
- **Telemetry**
  - `TELEMETRY_MODE` (default `noop`, allowed `noop|log`)
  - `TELEMETRY_SAMPLE_RATE` (default 1.0)

Note: `env.example` contains a verbose set of example values (including hardening toggles).

---

## 7) Testing & CI truth

### Pytest layout (truth from `backend/tests/`)

- Tests live in `backend/tests/` (unit + integration).
- `backend/tests/conftest.py` imports modular fixtures from `backend/tests/fixtures/`.

Key fixture behaviors:
- **Hermetic env by default**: `backend/tests/fixtures/env.py:isolate_test_env`
  - forces `APP_ENV=test`
  - sets `JWT_SECRET_KEY=test-secret-key`
  - clears `DATABASE_URL` and `REDIS_URL`
  - clears the cached settings (`get_settings.cache_clear()`) before/after each test
- **DB strategy**: `backend/tests/fixtures/db.py`
  - If `DATABASE_URL` is set in the test process, it is used (CI/Postgres mode).
  - Otherwise tests fall back to a temporary SQLite file.
  - For Postgres: migrations are applied via Alembic once per session.
  - For SQLite: schema is created via SQLAlchemy metadata.
- **HTTP integration**: `backend/tests/fixtures/fastapi_app.py`
  - builds the app via `create_app()`
  - overrides `get_db` to use the per-test `db_session`

### CI configuration (truth from repo contents)

- There is **no** `.github/workflows/` directory in this repository at baseline, so no GitHub Actions workflow definitions are versioned here.
- CI expectations are described in docs/tests (example: `backend/tests/README.md` mentions Postgres-backed runs via `DATABASE_URL`), but the actual CI pipeline configuration is not present in-repo.

---

## 8) Operational helper scripts

Scripts live under `scripts/` and are not part of runtime app behavior.

### `scripts/automated_tests/verify_prod_hardening.py`

- **Purpose**: A runtime verifier that checks key baseline behaviors against a running server.
- **Usage**:
  - `python scripts/automated_tests/verify_prod_hardening.py http://localhost:8000`
- **What it verifies (truth from script)**:
  - `GET /health` returns `200` and body exactly `{"status":"ok"}`
  - `GET /api/v1/health/live` returns `200`
  - `GET /api/v1/health/ready` returns `200`
  - `GET /api/v1/does-not-exist` returns `404` with standard error envelope and includes rate limit headers
  - Can create a v1 user, then login via `/api/v1/auth/login`
  - Cache demo calls `GET /api/v1/users/{id}` twice
  - Rate limiting demo attempts to observe a `429` on a v1 path

### `scripts/docker_logs/export_docker_logs_json.py`

- **Purpose**: Export Docker Compose service logs into machine-parseable JSON (`ndjson` or array) and save non-JSON lines separately.
- **Usage example**:
  - `python scripts/docker_logs/export_docker_logs_json.py --compose-cmd "docker compose" --service app --tail 200 --format ndjson --out app-logs.ndjson`

---

## 9) Known limitations / intentional non-features (as currently documented/implemented)

Truthful limitations in Phase 01 (confirmed in docs/code):
- **Legacy + v1 coexist**: Phase 01 shipped both `/api/v1/*` and some non-versioned routes.
- **Minimal RBAC**: `is_superuser` maps to `"admin"` (see `backend/docs/AUTH_MODEL.md` and `backend/app/auth/dependencies.py`).
- **Refresh tokens not included**: explicitly stated as not included yet in `backend/docs/AUTH_MODEL.md`.


