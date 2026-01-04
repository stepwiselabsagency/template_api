# PR Title
`feat: testing + CI baseline (pytest fixtures, unit/integration coverage, GitHub Actions)`

## Description
This PR implements **Milestone 7: Testing & CI** for the reusable FastAPI template. It standardizes pytest configuration, introduces **modular** shared fixtures (app/client/db/auth/optional redis), adds meaningful **unit + integration** test coverage, and provides a deterministic **GitHub Actions** pipeline that runs the same lint + test commands as local development.

Key non-negotiables preserved:
- Existing endpoints and successful response schemas remain unchanged (including legacy `/health` returning exactly `{"status":"ok"}`).
- `X-Request-ID` tracing remains intact and is asserted in integration tests.
- Standardized error schema remains intact and is asserted for 404/422 under `/api/v1`.
- Docker workflow remains intact (`make up/down/...`).

---

## Changes

### Pytest base configuration
- Added root `pytest.ini`:
  - Standardizes `testpaths` to `backend/tests`
  - Adds standard output options and markers (`unit`, `integration`)

### Modular shared fixtures (no giant `conftest.py`)
Refactored `backend/tests/conftest.py` to import fixtures from small modules under `backend/tests/fixtures/`:

- `backend/tests/fixtures/env.py`
  - Autouse `isolate_test_env` fixture to keep tests hermetic by default:
    - sets `APP_ENV=test`
    - sets `JWT_SECRET_KEY=test-secret-key`
    - clears `DATABASE_URL`/`REDIS_URL` so local runs don’t accidentally use a developer’s `.env`
    - clears `get_settings()` cache between tests

- `backend/tests/fixtures/db.py`
  - `database_url` (session): uses `DATABASE_URL` if provided; otherwise falls back to a temp SQLite DB
  - `db_engine` (session): creates SQLAlchemy engine from `database_url`
  - `db_schema` (session):
    - Postgres: runs **Alembic migrations** (`upgrade head`) for realistic schema coverage
    - SQLite fallback: uses `Base.metadata.create_all()` for local hermetic runs
  - `db_session` (function): deterministic rollback-only session per test
    - wraps each test in an outer transaction and ensures changes are rolled back
    - note: in tests, `Session.commit()` is treated as `flush()` so repository code that calls `commit()` still behaves correctly while remaining rollback-only per test

- `backend/tests/fixtures/fastapi_app.py`
  - `app`: creates FastAPI app via `create_app()` and overrides `get_db` to use `db_session`
  - `client`: `TestClient(app)`
  - ensures endpoints (like readiness) see the test `DATABASE_URL` by setting env + clearing settings cache before `create_app()`

- `backend/tests/fixtures/auth.py`
  - `test_user`: inserts an active user with known password (`pass123`)
  - `auth_headers`: logs in and returns `{"Authorization": "Bearer <token>"}`

- `backend/tests/fixtures/redis.py`
  - `redis_client`: optional fixture; skips if `REDIS_URL` is not configured or Redis isn’t reachable

### Unit tests (services + repositories)
Added unit tests under `backend/tests/unit/`:
- `test_user_repository.py`
  - create user
  - get by email
  - unique constraint behavior (duplicate email raises `IntegrityError`)
- `test_auth_service.py`
  - valid credentials authenticate
  - invalid credentials return `None`
  - inactive users cannot authenticate
- `test_jwt.py`
  - token includes `sub` and `exp`
  - expired token raises `ExpiredSignatureError` (accounting for decode leeway)

### Integration tests (API end-to-end)
Added Postgres-ready integration suite using the shared `client` + DB fixtures:
- `backend/tests/integration/test_api_integration.py`
  - Health:
    - `/health` returns `{"status":"ok"}`
    - `/api/v1/health/live` returns ok
    - `/api/v1/health/ready` returns ok + db check ok
  - User flow:
    - `POST /api/v1/users` (201)
    - `POST /auth/login` (200) returns token
    - `GET /api/v1/users/me` (200) returns user info
  - Error schema consistency:
    - 404 `/api/v1/does-not-exist` returns standard error schema including `request_id`
    - 422 validation error returns standard error schema including `request_id`

### Makefile improvements for test ergonomics (no behavior change)
`make test` still runs the full suite. Added explicit targets:
- `make test-unit`
- `make test-integration`

### GitHub Actions CI
Added `.github/workflows/ci.yml`:

- `lint` job:
  - installs deps via `pip install -e ".[dev]"`
  - runs `make lint`
  - runs Black/isort in check mode

- `test` job:
  - provisions Postgres 16 + Redis 7 via `services`
  - sets `DATABASE_URL` and `REDIS_URL` for test execution
  - runs `make test`

### Testing docs
Expanded `backend/tests/README.md` with:
- test pyramid (unit vs integration)
- how to run locally
- required/used env vars
- DB management strategy (migrations on Postgres + rollback-per-test)
- fixture inventory and how to extend
- CI overview + how to reproduce CI locally

---

## Milestone Completion Criteria
- [x] pytest base configuration + shared fixtures
- [x] unit tests for repositories/services/JWT
- [x] API integration tests (health, user flow, error schema, request id)
- [x] GitHub Actions CI (lint + tests with Postgres service)
- [x] Testing docs (`backend/tests/README.md`)

---

## Notes / Design Decisions
- **Template-friendly defaults**: tests do not require DB/Redis unless opted-in (CI opts-in via env vars).
- **CI realism**: Postgres runs migrations via Alembic to match production behavior.
- **Test isolation**: per-test DB isolation is achieved via rollback-only sessions; repository commits do not persist across tests.
- **Modularity**: fixtures are intentionally split into small modules under `backend/tests/fixtures/`.

---

## Validation Commands for Reviewer

```bash
# Local tooling
make fmt
make lint
make test
make precommit

# Optional targeted runs
make test-unit
make test-integration

# CI-like run locally (requires Postgres reachable)
# Example if using docker compose default credentials locally:
DATABASE_URL="postgresql+psycopg://app:app@localhost:5432/app" make test
```


