# PR Title
`feat: v1 public API baseline (/api/v1 routing + health probes + users endpoints + robust tests)`

## Description
This PR implements Milestone 5: **First complete functional API experience**. It introduces a clean, versioned API layer under **`/api/v1`** with health probes and foundational user endpoints, while preserving **backwards compatibility** for existing routes (`/health`, `/auth/login`, and existing non-versioned routers). It also strengthens test hygiene by making tests **environment-independent** and consistent in how they handle env variables.

## Changes
- **Versioned API routing (`backend/app/api/v1/`)**:
  - Added `backend/app/api/v1/router.py`:
    - `v1_router = APIRouter(prefix="/api/v1")`
    - Aggregates v1 subrouters:
      - `health_router` (mounted at `/api/v1/health/*`)
      - `users_router` (mounted at `/api/v1/users/*`)
  - Added `backend/app/api/v1/routes/`:
    - `health.py` (liveness + readiness)
    - `users.py` (create user + me + get-by-id)
  - Added `backend/app/api/v1/schemas/users.py` for request/response contracts.
  - Added `backend/app/api/v1/README.md` documenting:
    - versioning strategy (`/api/v1` now, `/api/v2` later)
    - router layout and how to add modules
    - endpoint examples and auth usage
    - common pitfalls (X-Request-ID, readiness vs liveness, 401/403/409)

- **Router wiring (app factory)**:
  - Updated `backend/app/core/app_factory.py` to mount `v1_router` (no API_PREFIX) while keeping existing `api_router` behavior intact:
    - Legacy `/health` remains unchanged (still returns `{"status":"ok"}`).
    - Existing routers mounted via `settings.API_PREFIX` remain as-is.
  - Startup dep-wait behavior hardened:
    - `_best_effort_wait_for_deps()` now only attempts psycopg connections for Postgres URLs (prevents odd behavior when tests use SQLite).

- **Health endpoints**
  - Added `GET /api/v1/health/live`
    - Always `200` with `{"status":"ok"}`; no DB/Redis dependency.
  - Added `GET /api/v1/health/ready`
    - Checks DB connectivity (required).
    - Checks Redis connectivity **only if configured** (`REDIS_URL` present).
    - Returns `200` with:
      - `{"status":"ok","checks":{"db":"ok","redis":"ok"}}`
    - Returns `503` with:
      - `{"status":"error","checks":{"db":"error","redis":"ok"}}` (or `redis:"error"` if configured+down)

- **User endpoints (v1)**
  - `POST /api/v1/users`
    - Creates a user using `UserRepository`
    - Hashes password using existing security utility
    - Returns `201` with a safe public user shape (no `hashed_password`)
    - Returns `409` on duplicate email
  - `GET /api/v1/users/me` (auth required)
    - Returns the current authenticated user (public shape)
  - `GET /api/v1/users/{user_id}` (auth required)
    - Authorization rule:
      - Allowed if requesting self, or user is superuser
      - Otherwise `403`

- **Tests (more robust + consistent env handling)**
  - Added shared test environment isolation:
    - `backend/tests/conftest.py` autouse fixture:
      - sets `APP_ENV=test`, `JWT_SECRET_KEY=test-secret-key`
      - clears `DATABASE_URL` and `REDIS_URL` by default
      - clears `get_settings()` cache before/after each test
  - Updated/added tests:
    - `backend/tests/test_health.py`
      - ensures legacy `/health` unchanged and includes `X-Request-ID`
    - `backend/tests/test_v1_health.py`
      - `/api/v1/health/live` returns 200 + `{"status":"ok"}`
      - `/api/v1/health/ready` returns:
        - `200` with SQLite DB configured
        - `503` when DB not configured
        - `503` when Redis configured but unreachable
    - `backend/tests/test_v1_users.py`
      - End-to-end: create user (v1) → login (legacy `/auth/login`) → call `/api/v1/users/me`
      - Duplicate email returns `409`
      - Fetching other user by id returns `403`; fetching self returns `200`
    - `backend/tests/test_persistence.py`
      - Kept hermetic by using SQLite unconditionally (no hidden dependency on external env)

## Milestone Completion Criteria
- [x] Versioned routing established at `/api/v1` with a clear router entrypoint (`v1_router`).
- [x] Health endpoints implemented:
  - [x] `/api/v1/health/live`
  - [x] `/api/v1/health/ready` (DB + optional Redis checks, 200/503 behavior)
- [x] User routes implemented:
  - [x] `POST /api/v1/users`
  - [x] `GET /api/v1/users/me`
  - [x] `GET /api/v1/users/{id}` with auth + authorization rules
- [x] v1 docs added at `backend/app/api/v1/README.md`
- [x] Backwards compatibility preserved:
  - [x] `/health` unchanged
  - [x] `/auth/login` unchanged
- [x] Tooling passes: `make fmt`, `make lint`, `make test`, `make precommit`

## Notes / Design Decisions
- **Backwards compatibility**: v1 routes were added in parallel; legacy routes remain and are not removed.
- **Readiness behavior**:
  - DB is required; readiness is `503` if `DATABASE_URL` is missing/unreachable.
  - Redis check is only enforced when `REDIS_URL` is configured; otherwise treated as `ok`.
- **Consistent test env strategy**:
  - Tests should not depend on a developer’s `.env` or Docker being up.
  - The shared `conftest.py` fixture standardizes env defaults and clears cached settings.

## Related
- Milestone: First complete functional API experience (v1 baseline)

---

## Validation Commands for Reviewer
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

# New v1 health
curl -i http://localhost:8000/api/v1/health/live
curl -i http://localhost:8000/api/v1/health/ready

# Create user (v1)
curl -i -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'

# Login (legacy OAuth2 form)
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=pass123"

# Me (v1) - replace <token>
curl -i http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <token>"