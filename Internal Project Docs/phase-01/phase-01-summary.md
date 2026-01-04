# Phase 1 Checkpoint — FastAPI Template Backend (Milestones 1–8)

**Last updated:** 2026-01-03  
**Purpose of this document:** single source of truth for what exists right now (features, structure, contracts, invariants). Phase 2 planning must treat this as the baseline.

## 0) What this project is

A reusable FastAPI backend template designed to be:

- Developer-friendly locally (Docker Compose + Makefile + pre-commit)
- Template-friendly for new products (clean architecture, explicit extension points)
- Production-minded by default (config, logging, request tracing, standardized errors)
- Optional-performance-ready (rate limiting, caching, telemetry — all opt-in)
- CI-backed (lint + tests on GitHub Actions with Postgres + Redis)

This is not a “feature product.” It’s a starter platform that other projects can fork/extend.

## 1) Phase 1 completion summary (Milestones 1–8 merged via PRs)

### Milestone 1 — Repo + Dev Tooling + Docker Compose

- FastAPI app initialized under `backend/`
- `docker-compose.yml` runs: app + Postgres 16 + Redis 7
- Make targets: `up`, `down`, `fmt`, `lint`, `test`, `precommit`
- Pre-commit configured (Black / isort / Ruff)
- Example env file exists and repo README provides quickstart + Windows/Git Bash guidance

### Milestone 2 — Core Application Architecture

`backend/app/core/` introduced as the backbone:

- Settings (pydantic-settings, cached accessor)
- Central logging (JSON/text) + request correlation via contextvars
- Middleware for X-Request-ID propagation + request logging
- App factory `create_app()` wiring everything cleanly
- Entrypoint stable: `uvicorn app.main:app`

### Milestone 3 — Persistence Layer

- SQLAlchemy 2.x + Alembic migrations
- Base User model + repository pattern
- Minimal legacy `/users` routes exist to prove DB wiring

### Milestone 4 — Secure Identity Foundation

- bcrypt hashing (passlib)
- JWT auth (HS256) issuance + verification (PyJWT)
- OAuth2 password login endpoint + `get_current_user` dependency
- Minimal RBAC baseline (`is_superuser` → "admin" role concept)
- Auth documented in `backend/docs/AUTH_MODEL.md`

### Milestone 5 — First Functional Public API Experience

- Versioned API introduced at `/api/v1`
- Health probes: `/api/v1/health/live` and `/api/v1/health/ready`
- V1 user endpoints: create, me, get-by-id with auth + authorization rules
- Backwards compatibility preserved (legacy `/health`, `/auth/login`, etc.)

### Milestone 6 — Production Hardening Layer

- Standard error response schema
- Global exception handlers
- Optional modules (off by default, fail-open if Redis issues):
  - Rate limiting (Redis backend)
  - Cache (Redis backend)
  - Telemetry hooks (noop/log)
- Docs + tests for this layer

### Milestone 7 — Testing & CI Baseline

- `pytest.ini` base config + markers
- Modular fixtures under `backend/tests/fixtures/`
- Unit + integration tests
- GitHub Actions CI:
  - lint job + test job
  - Postgres + Redis services in CI

### Milestone 8 — “Elite / LLM-friendly docs”

- High-signal docs suite in `backend/docs/`
- Folder-level READMEs added for navigation
- Root README upgraded to “start here” style
- No runtime behavior change in this milestone

## 2) Non-negotiable invariants (do not break in Phase 2)

These are contractual for this template:

### Legacy health endpoint remains unchanged

`GET /health` → exactly:

```json
{"status":"ok"}
```

### Request tracing

- Every response includes `X-Request-ID`
- If client sends `X-Request-ID`, it is echoed back

### Entrypoint stability

- Docker/compose runs `uvicorn app.main:app`

### Versioning strategy

- V1 public surface lives under `/api/v1`
- `/api/v2` is the future mechanism (not implemented yet)

### Standardized error envelope

- Errors handled by global handlers return a consistent envelope (tests assert this under `/api/v1`)

### Optional hardening features are opt-in

- Rate limiting / cache / telemetry are off by default
- When enabled, they are designed to be fail-open if Redis is unavailable (no self-inflicted outage)

### Tests must stay hermetic

- Tests should not silently depend on a developer’s `.env` or running Docker
- CI opts into Postgres/Redis via environment variables

## 3) Current repo structure (high-signal)

```text
repo-root/
|-- backend/
|   |-- app/
|   |   |-- api/                  # legacy (non-versioned) routing
|   |   |-- api/v1/               # versioned API surface (/api/v1)
|   |   |-- auth/                 # password + jwt + auth deps + auth service
|   |   |-- core/                 # settings/logging/middleware/errors/hardening wiring
|   |   |-- db/                   # SQLAlchemy engine/session + Base
|   |   |-- models/               # User model (+ import side-effects for Alembic)
|   |   |-- repositories/         # BaseRepository + UserRepository
|   |-- alembic/                  # migrations
|   |-- docs/                     # onboarding + architecture + error + rate-limit + auth docs
|   |-- tests/                    # unit + integration tests + fixtures/
|-- scripts/                      # repo utilities (log export, verification helpers, etc.)
|-- .github/workflows/ci.yml      # lint + test pipeline
|-- docker-compose.yml
|-- Dockerfile
|-- Makefile
|-- pyproject.toml
|-- .env.example                  # canonical example env (copy to .env)
```

## 4) Runtime architecture (what is wired today)

### App creation path

`backend/app/main.py` exposes:

- `app = create_app()`

`backend/app/core/app_factory.py` owns assembly:

- loads settings
- configures logging
- registers exception handlers
- wires middleware
- mounts routers (legacy + `/api/v1`)

### Settings

`backend/app/core/config.py`

- Pydantic v2 pydantic-settings
- `get_settings()` is cached (tests clear cache between runs)
- `model_dump_safe()` redacts secrets (e.g., JWT secret)

### Middleware (key behaviors)

Request ID middleware:

- reads incoming `X-Request-ID` or generates UUID
- stores in contextvars
- always sets response header `X-Request-ID`

Request logging middleware:

- one summary log line per request
- exception logging uses request id context

Note: Starlette middleware is applied in reverse order; middleware ordering is documented in `backend/app/core/README.md` and `backend/docs/ARCHITECTURE.md`.

## 5) Persistence layer (what exists)

### Database + sessions

- SQLAlchemy 2.x engine/session patterns in `backend/app/db/session.py`
- `get_db()` FastAPI dependency:
  - session-per-request
  - closes session in finally

### Models

User model exists in `backend/app/models/user.py`:

- id UUID primary key
- email unique + indexed + not null
- hashed_password not null
- is_active boolean default true
- is_superuser boolean default false
- timestamps (created_at, updated_at) timezone-aware

### Migrations

- Alembic configured under `backend/alembic/`
- At least two migrations exist:
  - create users table
  - add is_superuser

### Repository pattern

UserRepository supports:

- get_by_id, get_by_email, create, list, set_active

## 6) Auth model (what exists)

### Password hashing

- `passlib[bcrypt]`
- `hash_password()` / `verify_password()` live in `backend/app/auth/password.py`
- `backend/app/core/security.py` remains as a wrapper for compatibility

### JWT

- HS256 via PyJWT
- `create_access_token()` / `decode_token()` in `backend/app/auth/jwt.py`
- Conservative validation:
  - requires sub
  - validates exp
  - optional issuer/audience supported via settings

### Login + current user

`POST /auth/login`

- OAuth2 password flow (`application/x-www-form-urlencoded`)
- uses username as email
- returns:

```json
{"access_token":"...","token_type":"bearer","expires_in":3600}
```

`GET /auth/me`

- protected route returning user basics

### RBAC baseline

- Minimal mapping:
  - is_superuser → "admin"-like capability
  - `require_roles("admin")` supported

Auth is documented in `backend/docs/AUTH_MODEL.md`.

## 7) Public API surface (current endpoints)

### Legacy (non-versioned) endpoints

These exist primarily for backward compatibility and template bootstrapping:

`GET /health`  
Returns exactly:

```json
{"status":"ok"}
```

Also includes `X-Request-ID` header.

`POST /auth/login`  
OAuth2 form login (email in username).

`GET /auth/me`  
Requires `Authorization: Bearer <token>`.

Legacy `/users` routes exist (from persistence milestone) and may still be present depending on current router wiring. Phase 2 should treat `/api/v1/users/*` as the stable public surface.

### Versioned v1 endpoints (`/api/v1`)

#### Health

`GET /api/v1/health/live`

Always 200:

```json
{"status":"ok"}
```

`GET /api/v1/health/ready`

- DB is required:
  - 200 when DB reachable
  - 503 when DB missing/unreachable
- Redis is checked only if configured (`REDIS_URL` set)

Response shape:

```json
{"status":"ok","checks":{"db":"ok","redis":"ok"}}
```

or on failure:

```json
{"status":"error","checks":{"db":"error","redis":"ok"}}
```

#### Users

`POST /api/v1/users`

- Creates user
- Hashes password
- Returns public user shape (never returns hashed_password)
- Duplicate email returns 409

`GET /api/v1/users/me`

- Auth required

`GET /api/v1/users/{user_id}`

- Auth required
- Authorization:
  - allowed if requesting self OR user is superuser
  - otherwise 403

## 8) Standard error model (what is true today)

A standardized error envelope exists (via global exception handlers). The canonical shape:

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

`request_id` matches the `X-Request-ID` header.

Mapping includes (at minimum):

- 422 → validation_error
- 401 → unauthorized (preserves `WWW-Authenticate: Bearer`)
- 403 → forbidden
- 404 → not_found
- 409 → conflict (including optional IntegrityError mapping)
- 429 → rate_limited
- 500 → internal_error

Tests explicitly assert standardized errors under `/api/v1` (404/422).

Canonical docs:

- `backend/docs/ERROR_MODEL.md`
- `backend/app/core/exception_handlers.py`
- `backend/app/core/errors.py`

## 9) Optional production hardening modules (present but off by default)

### Rate limiting (optional)

Protocol + Redis backend + middleware exist under:

- `backend/app/core/rate_limit/`

Scope:

- applied to `/api/v1/*` only
- excludes:
  - `/health`
  - `/api/v1/health/live`
  - `/api/v1/health/ready`

Headers when enabled:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

Exceeded returns 429 with standard error envelope (code="rate_limited")

Fail-open if Redis errors

Docs: `backend/docs/RATE_LIMITING.md`

### Cache (optional)

Interface + Redis cache + dependency exist under:

- `backend/app/core/cache/`

Demonstration usage:

- `GET /api/v1/users/{id}` caches the authorized public payload when enabled

Fail-open if Redis errors

### Telemetry (vendor-neutral)

Protocol-based telemetry:

- default noop
- optional log mode

Middleware emits:

- request counters + duration metrics (conceptually)

Designed as an integration seam for real observability later

Docs index: `backend/docs/PROD_HARDENING.md` (overview) + architecture doc.

## 10) Developer workflow (how to run and validate)

### Local quickstart

```bash
cp .env.example .env
make up
curl http://localhost:8000/health
```

### Tooling

```bash
make fmt
make lint
make test
make precommit
```

### DB migrations

```bash
make db-upgrade
make db-revision msg="your message"
make db-downgrade
```

## 11) Testing + CI truth

### Pytest design

`pytest.ini` defines:

- `testpaths = backend/tests`
- markers for unit and integration

### Fixtures (modular)

Located under `backend/tests/fixtures/`:

- `env.py`: hermetic environment defaults + clears cached settings
- `db.py`: database URL selection + engine + schema setup
  - uses Postgres migrations when Postgres configured (CI)
  - SQLite fallback for local hermetic runs
- `fastapi_app.py`: builds app via `create_app()` and overrides `get_db`
- `auth.py`: creates test user + returns auth headers
- `redis.py`: optional redis fixture (skips if unavailable)

### CI pipeline

`.github/workflows/ci.yml`

lint job:

- installs `pip install -e ".[dev]"`
- runs `make lint` + Black/isort checks

test job:

- starts Postgres 16 + Redis 7 services
- sets `DATABASE_URL` and `REDIS_URL`
- runs `make test`

Goal: local commands mirror CI behavior.

## 12) Key environment variables (baseline)

Canonical list is in `.env.example`. These are the important categories the template currently supports.

### Core

- `APP_ENV` (e.g., local, test, prod)
- `LOG_LEVEL`, `LOG_JSON` (logging mode)
- (request-id behavior is middleware-driven; config may include related toggles)

### Database / Redis

- `DATABASE_URL`
- `REDIS_URL` (optional unless readiness/rate-limit/cache enabled)

### JWT/Auth

- `JWT_SECRET_KEY` (required outside local/test conventions)
- `JWT_ALGORITHM` (default HS256)
- `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` (default 60)
- Optional: `JWT_ISSUER`, `JWT_AUDIENCE`

### Hardening (all optional / default off)

Rate limiting:

- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_REQUESTS`
- `RATE_LIMIT_WINDOW_SECONDS`
- (may include key strategy options depending on implementation)

Cache:

- `CACHE_ENABLED`
- `CACHE_DEFAULT_TTL_SECONDS`

Telemetry:

- `TELEMETRY_MODE` (noop / log)
- `TELEMETRY_SAMPLE_RATE`

## 13) What is intentionally NOT in Phase 1

This is important so Phase 2 planning doesn’t assume it exists:

- Refresh tokens, token rotation, sessions, device tracking
- Email verification / password reset flows
- Full RBAC/ABAC system (only minimal is_superuser baseline)
- User update/delete, pagination, filtering, admin endpoints
- Multi-tenant data model
- Background jobs / worker system
- OpenTelemetry/Prometheus exporters (telemetry is only a hook seam right now)
- Cloud deployment manifests (this template is cloud-ready-by-design, but not cloud-deployed in Phase 1)

## 14) Phase 2 planning notes (constraints for the next plan)

When generating Phase 2 milestones, the plan must:

- Preserve all invariants listed in Section 2
- Treat `/api/v1/*` as the stable public surface
- Keep hardening modules optional and avoid making Redis a single point of failure
- Keep tests hermetic and CI reproducible
- Extend via documented extension points:
  - `backend/app/api/v1/routes/`
  - `backend/app/api/v1/schemas/`
  - `backend/app/repositories/`
  - `backend/app/core/*` only when truly cross-cutting

## 15) Where to read inside the repo (docs map)

Start here:

- `backend/docs/ONBOARDING.md`

Architecture truth:

- `backend/docs/ARCHITECTURE.md`

Error contract truth:

- `backend/docs/ERROR_MODEL.md`

Auth truth:

- `backend/docs/AUTH_MODEL.md`

Rate limit truth:

- `backend/docs/RATE_LIMITING.md`

Hardening overview:

- `backend/docs/PROD_HARDENING.md`

End of Phase 1 checkpoint.


