# backend/tests — Testing & CI

This repository is a reusable FastAPI backend template. The test suite is
designed to be **fast**, **deterministic**, and **easy to extend**.

## Test pyramid

- **Unit tests** (`backend/tests/unit/`)
  - Pure logic tests (JWT, auth service, repository behavior)
  - No HTTP server required
  - Use a rollback-only DB session when DB behavior matters (unique constraints)

- **Integration tests** (`backend/tests/` and `backend/tests/*`)
  - Full HTTP tests using `fastapi.testclient.TestClient`
  - Verifies request id middleware (`X-Request-ID`), error schema, and core routes

## Running tests locally

From the repo root:

```bash
make test
```

Targeted runs:

```bash
pytest -k jwt
pytest backend/tests/unit -q
pytest backend/tests -q
```

Make targets:

```bash
make test-unit
make test-integration
```

## Environment variables used in tests

Tests default to a hermetic environment (they do **not** read your `.env`).

- `APP_ENV`: set to `test` by default
- `JWT_SECRET_KEY`: set to `test-secret-key` by default
- `DATABASE_URL`: cleared by default; some tests opt-in explicitly
- `REDIS_URL`: cleared by default; some tests opt-in explicitly

In CI, we run DB-backed tests against Postgres by providing `DATABASE_URL` to the
pytest session-scoped DB fixtures.

## Database strategy in tests

We support two modes:

- **CI / Postgres mode (preferred)**
  - Uses `DATABASE_URL` pointing at Postgres
  - Runs **Alembic migrations** once per test session
  - Each test runs inside a **nested transaction** (SAVEPOINT) and rolls back

- **Local fallback / SQLite mode**
  - If `DATABASE_URL` is not set for the pytest process, tests fall back to a
    temporary SQLite file.
  - We create the schema with `Base.metadata.create_all()` (because current
    migrations include Postgres-only SQL such as `now()`).

Relevant fixtures:

- `database_url` (session): resolved DB URL
- `db_engine` (session): SQLAlchemy engine
- `db_schema` (session): ensures schema exists (migrations on Postgres, create_all on SQLite)
- `db_session` (function): rollback-only Session per test

## Common fixtures

These live under `backend/tests/fixtures/` and are imported by
`backend/tests/conftest.py`:

- `app`: `create_app()` wired to `db_session` via dependency override
- `client`: `TestClient(app)`
- `test_user`: a DB user with known password (`pass123`)
- `auth_headers`: `{"Authorization": "Bearer <token>"}`

## CI overview

GitHub Actions runs:

- **lint**: Black check, isort check, Ruff
- **test**: pytest (unit + integration) with Postgres service

To reproduce CI locally, start Postgres (e.g., via `make up`) and run:

```bash
DATABASE_URL="postgresql+psycopg://app:app@localhost:5432/app" make test
```

