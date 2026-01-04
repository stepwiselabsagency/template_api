# Phase 01 Checkpoint — FastAPI Template Backend (Milestones 1–8)

**Checkpoint date:** 2026-01-03  
**Scope of this document:** A complete, LLM-friendly description of what exists today (code, behavior, structure, scripts, tests, CI, docs).  
No Phase 02 planning is included.

## 1) What this repository is

A reusable FastAPI backend template that provides:

- A clean application skeleton with a clear `app/core/` backbone
- A working persistence layer (SQLAlchemy 2.x + Alembic)
- A baseline auth system (bcrypt + JWT + OAuth2 password login)
- A versioned public API surface under `/api/v1`
- A "production hardening" layer:
  - consistent error envelope + global exception handlers
  - optional rate limiting, cache, and telemetry hooks
- A serious testing + CI baseline (unit + integration + GitHub Actions)
- A documentation suite designed to be LLM-friendly and onboarding-ready

This repo is intended to be forked or used as a base for other services.

## 2) Phase 01 milestones completed (PR history condensed)

### Milestone 1 — Repo + Dev Tooling + Docker Compose

**Delivered**

- `backend/` FastAPI app skeleton
- `docker-compose.yml` + `Dockerfile` for local stack:
  - app, Postgres 16, Redis 7
- Makefile targets (at minimum):
  - `up`, `down`, `fmt`, `lint`, `test`, `precommit`
- Tooling pinned in `pyproject.toml`:
  - Black, isort, Ruff, pytest (+ runtime deps as needed later)
- `.pre-commit-config.yaml` configured
- `.env.example` with working local defaults
- Root `README.md` with quickstart + ports + Windows/Git Bash troubleshooting

**Invariant introduced**

- `GET /health` returns exactly:
  ```json
  {"status":"ok"}
  ```

### Milestone 2 — Core Application Architecture

**Delivered**

- `backend/app/core/` backbone:
  - `config.py` using pydantic-settings (Pydantic v2 style)
    - cached `get_settings()` accessor
    - safe dump/redaction utility
  - `logging.py` + correlation via contextvars
  - middleware:
    - request id middleware (incoming `X-Request-ID` or generated UUID; always returned)
    - request logging middleware (summary logs + exception logging)
  - `app_factory.py` with `create_app()` (single wiring point)
- `backend/app/main.py` exposes:
  - `app = create_app()`
- Entrypoint stability preserved (`uvicorn app.main:app`)

**Behavior**

- Every response includes `X-Request-ID`
- If `X-Request-ID` is provided, it is echoed back

### Milestone 3 — Persistence Layer (SQLAlchemy + Alembic + Repos + minimal users wiring)

**Delivered**

- `backend/app/db/`
  - `base.py` (Base)
  - `session.py`:
    - engine creation from settings / `DATABASE_URL`
    - session factory (SessionLocal)
    - `get_db()` dependency (session-per-request, closed in finally)
- `backend/app/models/`
  - User model (UUID PK, email unique/indexed, hashed_password, is_active, timestamps)
  - `app/models/__init__.py` imports models so Alembic autogenerate can discover metadata
- Alembic:
  - `backend/alembic.ini`
  - `backend/alembic/env.py` targets Base.metadata and loads DB URL from settings
  - initial migration creates users table
- `backend/app/repositories/`
  - BaseRepository helpers
  - UserRepository methods include:
    - `get_by_id`, `get_by_email`, `create`, `list`, `set_active`
- Minimal legacy `/users` endpoints exist as "DB wiring proof" (later `/api/v1/users/*` becomes the stable public surface)

**Design notes**

- UUID stored as Postgres-native UUID (`Uuid(as_uuid=True)`) when on Postgres
- Email validation kept as `str` to avoid adding email-validator dependency (template stays slim)

### Milestone 4 — Secure Identity Foundation (bcrypt + JWT + login + auth deps)

**Delivered**

- `backend/app/auth/`:
  - `password.py`: bcrypt hashing via `passlib[bcrypt]`
  - `jwt.py`: JWT create/decode using PyJWT (HS256 default)
  - `service.py`: user auth + token issuance
  - `dependencies.py`: `get_current_user` and minimal role gating (`require_roles`)
- API routes:
  - `POST /auth/login` using `OAuth2PasswordRequestForm`
    - Content-Type: `application/x-www-form-urlencoded`
    - treats username as email
  - `GET /auth/me` protected route
- User model updated with `is_superuser` + migration
- `backend/app/core/security.py` kept as compatibility wrapper exporting hash/verify from `auth/password.py`
- Docs added: `backend/docs/AUTH_MODEL.md`

**Security behavior**

- invalid credentials and inactive users return 401 (no user-status leakage)
- on auth failures, response preserves `WWW-Authenticate: Bearer` header (important for standards + clients)

### Milestone 5 — First Complete Functional API Experience (Versioned /api/v1)

**Delivered**

- Versioned routing:
  - `backend/app/api/v1/router.py` (`APIRouter(prefix="/api/v1")`)
  - `backend/app/api/v1/routes/` (health + users)
  - `backend/app/api/v1/schemas/` for request/response contracts
  - `backend/app/api/v1/README.md` with versioning rules and examples
- Health endpoints:
  - `GET /api/v1/health/live` → always 200 `{"status":"ok"}`
  - `GET /api/v1/health/ready`
    - DB connectivity required
    - Redis check only if `REDIS_URL` configured
    - 200 on OK, 503 on failure, with explicit checks object
- Users (v1):
  - `POST /api/v1/users` (create, 409 on duplicate email)
  - `GET /api/v1/users/me` (auth required)
  - `GET /api/v1/users/{user_id}` (auth required)
    - authorization: self OR superuser, else 403
- Backwards compatibility preserved:
  - `/health` unchanged
  - `/auth/login` unchanged
- Startup dep-wait logic hardened:
  - only attempts Postgres connectivity when `DATABASE_URL` is Postgres (prevents odd behavior when tests use SQLite)

### Milestone 6 — Production Hardening (Errors + Exception Handling + Optional Rate Limit/Cache/Telemetry)

**Delivered**

- Standard error envelope:
  - `backend/app/core/errors.py` defines stable schema + helpers + status→code mapping
- Global exception handlers:
  - `backend/app/core/exception_handlers.py` registered in app factory
  - Handles at least:
    - `RequestValidationError` → 422 standardized error with safe details
    - `HTTPException` → standardized error (preserving critical headers)
    - unexpected exceptions → 500 standardized error (no internal leakage; logs stack trace)
    - optional: `IntegrityError` → 409 standardized error
- Optional modules (all off by default):
  - **Rate limiting** (`backend/app/core/rate_limit/`)
    - interface + Redis backend (atomic Lua fixed-window)
    - middleware scopes to `/api/v1/*` and excludes health endpoints
    - adds rate-limit headers; 429 uses standard error envelope
    - fail-open if Redis errors
  - **Cache** (`backend/app/core/cache/`)
    - interface + Redis cache
    - demo wiring: caches `GET /api/v1/users/{id}` after authorization
    - caches only the public payload (never request-specific)
    - fail-open if Redis errors
  - **Telemetry** (`backend/app/core/telemetry.py`, `telemetry_middleware.py`)
    - vendor-neutral protocol
    - noop default + logging-based implementation option
    - emits request counters + timing metrics through the interface
- Docs added/updated:
  - `backend/docs/PROD_HARDENING.md` (overview + enablement)
- Tests added for:
  - standardized errors (404/422) under `/api/v1`
  - rate limiting behavior (enabled/disabled)
  - cache behavior (enabled)
  - telemetry interface being called

**Important runtime invariants preserved**

- `GET /health` remains exactly `{"status":"ok"}`
- successful responses are not changed by hardening; only error responses are standardized via handlers
- `X-Request-ID` appears in standardized error bodies as well

### Milestone 7 — Testing & CI Baseline

**Delivered**

- `pytest.ini` baseline configuration + markers
- Fixtures split under `backend/tests/fixtures/` (avoid giant `conftest.py`):
  - `env.py` (autouse):
    - sets `APP_ENV=test`
    - sets `JWT_SECRET_KEY=test-secret-key`
    - clears `DATABASE_URL` and `REDIS_URL` by default (prevents leaking dev env into tests)
    - clears `get_settings()` cache between tests
  - `db.py`:
    - session database_url uses env if provided; else temp SQLite file
    - schema setup:
      - Postgres: runs Alembic migrations (CI realism)
      - SQLite fallback: `Base.metadata.create_all()`
    - per-test rollback isolation strategy:
      - wraps each test in transaction(s) so repository `.commit()` behaves but state is rolled back per test
  - `fastapi_app.py`:
    - creates app via `create_app()`
    - overrides `get_db` to use test session
    - ensures readiness checks see the correct test DB URL (env + cache clearing)
  - `auth.py`:
    - creates a test user (`pass123`) and returns Authorization headers after login
  - `redis.py`:
    - optional fixture that skips if Redis not configured/reachable
- Tests added:
  - Unit tests for repo/service/jwt behaviors
  - Integration tests covering:
    - `/health`, `/api/v1/health/live`, `/api/v1/health/ready`
    - create user → login → `/api/v1/users/me`
    - error envelope for 404/422 under `/api/v1`
    - `X-Request-ID` present/propagated
- Make targets extended for test ergonomics:
  - `make test` (full suite)
  - `make test-unit`
  - `make test-integration`
- GitHub Actions `.github/workflows/ci.yml`:
  - lint job:
    - installs `pip install -e ".[dev]"`
    - runs `make lint`
    - runs Black + isort in check mode
  - test job:
    - uses Postgres service + Redis service
    - sets `DATABASE_URL` and `REDIS_URL`
    - runs `make test`

### Milestone 8 — Elite Docs + Folder READMEs (docs-only; no behavior change)

**Delivered**

- Central docs hub: `backend/docs/` including (at minimum):
  - `ONBOARDING.md` (fast onboarding path + "where do I change X")
  - `ARCHITECTURE.md` (request flow + extension points + invariants)
  - `ERROR_MODEL.md` (single source of truth for standardized errors)
  - `RATE_LIMITING.md` (enablement + scope + headers + algorithm)
  - `PROD_HARDENING.md` (overview + cross-links)
  - `AUTH_MODEL.md` (auth claims + flows + curl examples)
- Folder-level READMEs added across major directories to make navigation obvious
- Root README upgraded with a "Start here" onboarding path and docs index
- Documentation reconciled to avoid contradictions/drift

## 3) Current public behavior: endpoints and contracts

### 3.1 Legacy endpoints (backwards compatible)

**GET /health**  
Response (exact):

```json
{"status":"ok"}
```

Also: `X-Request-ID` header present

**POST /auth/login**

- Content-Type: `application/x-www-form-urlencoded`
- body includes: `username=<email>&password=<password>`
- success returns `{access_token, token_type, expires_in}` (shape is stable)

**GET /auth/me**

- requires `Authorization: Bearer <token>`

Legacy `/users` endpoints exist as earlier DB proof routes; the stable versioned surface is `/api/v1/users/*`.

### 3.2 Versioned API (/api/v1)

**Health**

- `GET /api/v1/health/live`
  - always 200:
    ```json
    {"status":"ok"}
    ```
- `GET /api/v1/health/ready`
  - DB required
  - Redis checked only if configured (`REDIS_URL` set)
  - success:
    ```json
    {"status":"ok","checks":{"db":"ok","redis":"ok"}}
    ```
  - failure (example):
    ```json
    {"status":"error","checks":{"db":"error","redis":"ok"}}
    ```
  - failure status code: 503

**Users**

- `POST /api/v1/users`
  - creates user (bcrypt hashes password)
  - returns safe public user shape (no password hash)
  - duplicate email → 409
- `GET /api/v1/users/me`
  - auth required
- `GET /api/v1/users/{user_id}`
  - auth required
  - allowed if:
    - requesting self OR requester is superuser
  - otherwise 403
  - may be cached (only if cache enabled), after authorization

## 4) Error behavior: standardized envelope (current truth)

For handled errors (via global exception handlers), the response body is:

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

**Key properties:**

- `request_id` matches `X-Request-ID`
- `HTTPException` handler standardizes across status codes (including 404)
- 401 preserves `WWW-Authenticate: Bearer`
- 500 response never leaks internals, but logs include stack trace with request correlation

**The canonical docs/code:**

- `backend/docs/ERROR_MODEL.md`
- `backend/app/core/exception_handlers.py`
- `backend/app/core/errors.py`

## 5) Hardening modules: what exists and how it behaves

### 5.1 Rate limiting (optional, off by default)

**Location:**

- `backend/app/core/rate_limit/`
  - `interface.py` (protocol)
  - `redis_backend.py` (atomic fixed-window using Lua)
  - `middleware.py`
  - builder in `__init__.py`

**Behavior:**

- Applied to `/api/v1/*` only
- Excludes:
  - `/health`
  - `/api/v1/health/live`
  - `/api/v1/health/ready`
- Adds headers when enabled:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`
- On exceed: 429 with standard error (code="rate_limited")
- Fail-open if Redis has issues (rate limiter never becomes an outage cause)

**Docs:**

- `backend/docs/RATE_LIMITING.md`

### 5.2 Cache (optional, off by default)

**Location:**

- `backend/app/core/cache/`
  - `interface.py`
  - `redis_cache.py`
  - `dependency.py` (`get_cache`)
  - builder in `__init__.py`

**Behavior:**

- Demonstration wiring in `GET /api/v1/users/{id}`:
  - caches only authorized responses
  - caches only the public payload (no request-specific fields)
  - TTL is conservative/short-lived by default

### 5.3 Telemetry hooks (optional mode; default noop)

**Location:**

- `backend/app/core/telemetry.py`
- `backend/app/core/telemetry_middleware.py`

**Behavior:**

- Protocol-driven "telemetry sink"
- Default: `NoopTelemetry`
- Optional: `LoggingTelemetry` that emits structured metric log lines
- Middleware emits request count + duration events through the telemetry interface
- Sampling supported via settings (when configured)

## 6) Persistence layer: what exists

**Database/session lifecycle**

- Engine/session built from settings `DATABASE_URL`
- `get_db()` provides a per-request session and closes it safely

**User model**

User includes:

- `id` UUID (primary key)
- `email` unique/indexed
- `hashed_password`
- `is_active` (default true)
- `is_superuser` (default false)
- `created_at`, `updated_at` (tz-aware)

**Migrations live under:**

- `backend/alembic/versions/`

## 7) Logging + request correlation (current truth)

- Request id stored via contextvars
- Middleware ensures `X-Request-ID` header is always returned
- When JSON logging is enabled (e.g., `LOG_JSON=true`), logs emit one JSON object per line
- Request logs and exception logs include request correlation (request id)
- This is used directly in the "docker logs export" workflow described below.

## 8) Developer workflow: commands and operational helpers

**Core commands**

```bash
make up
make down
make fmt
make lint
make test
make precommit
```

**Alembic helpers (Docker-aligned workflow)**

```bash
make db-upgrade
make db-revision msg="your message"
make db-downgrade
```

**CI parity locally (example)**

- CI sets `DATABASE_URL` + `REDIS_URL` and runs `make test`
- Locally you can reproduce CI-like behavior by exporting these env vars and running `make test`

## 9) Testing system: what is special/important

**Hermetic test defaults (very important)**

- Tests do not automatically use your `.env` values
- Autouse fixture sets `APP_ENV=test`, sets a test JWT secret, and clears DB/Redis env vars by default
- Settings cache is cleared between tests so env changes are respected

**DB strategy**

- If Postgres is configured (CI), tests apply Alembic migrations for realism
- If not, tests fall back to a temp SQLite DB for local convenience

**Rollback-per-test isolation**

- Test session strategy ensures each test is isolated:
  - repository code that calls `commit()` still behaves correctly
  - but state is rolled back/reset between tests

**Integration coverage (current truth)**

Integration tests validate:

- `/health` exact response + request id header
- `/api/v1/health/live` and `/api/v1/health/ready`
- v1 user flow: create → login → me
- standardized error envelope for 404/422 under `/api/v1`

**Docs:**

- `backend/tests/README.md` (test pyramid, how to run, fixtures inventory, CI notes)

## 10) Repo scripts that matter (Phase 01 includes working verification utilities)

Phase 01 includes notable Python scripts used for validation and debugging beyond unit/integration tests.

### 10.1 Production hardening verification script

**Path:**

- `scripts/automated_tests/verify_prod_hardening.py`

**Purpose:**

Automated end-to-end verification against a running base URL, typically to confirm:

- standardized error schema exists (404/422)
- rate limiting triggers 429 + headers when enabled
- cache writes keys when enabled (in combination with user flow)
- auth flow works (create user → login → protected call)

**Typical usage pattern:**

```bash
python scripts/automated_tests/verify_prod_hardening.py http://localhost:8000
```

This script is used as a "black box verifier" for the hardening layer when environment toggles are enabled.

### 10.2 Docker logs export / JSON cleaning utility

**Path:**

- `scripts/docker_logs/export_docker_logs_json.py`

**Problem it solves:**

- `docker-compose logs` prefixes and non-JSON lines can break log parsing.

This script exports the last N lines and produces a clean JSON output:

- either a JSON array of parsed objects, or NDJSON
- with dropped-line reporting for non-JSON lines

**Example usage patterns (as documented in Phase 01):**

```bash
python scripts/docker_logs/export_docker_logs_json.py \
  --compose-cmd "docker-compose" \
  --service app \
  --tail 200 \
  --format array \
  --out app-logs-200.json \
  --dropped-out app-logs-200.dropped.txt
```

or:

```bash
python scripts/docker_logs/export_docker_logs_json.py \
  --compose-cmd "docker-compose" \
  --service app \
  --tail 200 \
  --format ndjson \
  --out app-logs-200.ndjson \
  --dropped-out app-logs-200.dropped.txt
```

This is part of the Phase 01 "logs analysis" workflow to confirm:

- JSON logs exist when enabled
- `request_id` propagation appears in logs and correlates with responses
- telemetry log events appear when telemetry is enabled in log mode

## 11) GitHub Actions CI (current truth)

**Workflow file:**

- `.github/workflows/ci.yml`

**Jobs:**

- **lint**
  - checkout
  - setup python 3.11
  - install `pip install -e ".[dev]"`
  - run `make lint`
  - run Black + isort in check mode
- **test**
  - services: Postgres + Redis
  - env provides `DATABASE_URL` and `REDIS_URL`
  - runs `make test`

CI is aligned with local Make targets.

## 12) Documentation map (what exists and where)

**Docs home:**

- `backend/docs/`

**Key docs (Phase 01 truth sources):**

- `backend/docs/ONBOARDING.md` — shortest path to "productive"
- `backend/docs/ARCHITECTURE.md` — request flow, subsystems, invariants, extension points
- `backend/docs/ERROR_MODEL.md` — standardized error envelope and mapping rules
- `backend/docs/RATE_LIMITING.md` — enablement, scope rules, headers, algorithm
- `backend/docs/PROD_HARDENING.md` — overview/index (cross-links)
- `backend/docs/AUTH_MODEL.md` — password hashing, JWT claims, login flow, curl examples

Folder READMEs exist across major directories (`backend/app` submodules, `scripts`, etc.) to make navigation obvious.

## 13) Project structure (high-signal)

```text
repo-root/
|-- backend/
|   |-- app/
|   |   |-- api/                    # legacy routes + router
|   |   |-- api/v1/                 # versioned API (/api/v1) router + routes + schemas
|   |   |-- auth/                   # bcrypt + jwt + auth services + auth dependencies
|   |   |-- core/                   # settings/logging/middleware/errors/hardening wiring
|   |   |-- db/                     # SQLAlchemy engine/session + Base
|   |   |-- models/                 # User model (+ import side-effects for Alembic)
|   |   |-- repositories/           # BaseRepository + UserRepository
|   |-- alembic/                    # Alembic env + versions/
|   |-- docs/                       # onboarding + architecture + error model + etc.
|   |-- tests/                      # unit + integration + fixtures/
|-- scripts/
|   |-- automated_tests/            # runtime verification utilities
|   |-- docker_logs/                # log export/cleanup utilities
|-- .github/workflows/ci.yml
|-- docker-compose.yml
|-- Dockerfile
|-- Makefile
|-- pyproject.toml
|-- .env.example
`-- README.md
```

## 14) "Do not accidentally change" behaviors (Phase 01 truth constraints)

These are currently relied on by tests/docs/scripts and should be treated as stable facts of Phase 01:

- `GET /health` returns exactly `{"status":"ok"}`
- `X-Request-ID` always present and echoes incoming value
- `/api/v1` routing exists and contains:
  - `/api/v1/health/live`
  - `/api/v1/health/ready`
  - `/api/v1/users` create
  - `/api/v1/users/me`
  - `/api/v1/users/{id}` with self-or-superuser rule
- Standard error envelope exists for handled errors (and is asserted in tests under `/api/v1`)
- Optional hardening modules are present and default off; when enabled they do not break successful response schemas

End of Phase 01 checkpoint (complete context only).
