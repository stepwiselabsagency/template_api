# `backend/` — Python service package + migrations + tests

- **Purpose**: Everything required to build, run, test, and migrate the FastAPI backend.

## Purpose

- Owns the application package under `backend/app/`
- Owns migrations under `backend/alembic/` + config `backend/alembic.ini`
- Owns the test suite under `backend/tests/`
- Owns template docs under `backend/docs/`

## Key modules/files

- **App entrypoint**: `backend/app/main.py`
- **App factory**: `backend/app/core/app_factory.py`
- **Alembic**: `backend/alembic/env.py`, `backend/alembic/versions/`
- **Tests**: `backend/tests/`
- **Docs**: `backend/docs/`

## How it connects

- Root `Dockerfile` and `docker-compose.yml` run this backend package.
- Root `Makefile` targets (fmt/lint/test/db-*) operate on this backend.

## Extension points

- **Add v2 API**: create `backend/app/api/v2/` and include it from `backend/app/core/app_factory.py`.
- **Add a new DB model**: add file under `backend/app/models/` and import it in `backend/app/models/__init__.py`.
- **Add middleware**: implement in `backend/app/core/` and wire ordering in `backend/app/core/app_factory.py`.

## Pitfalls / invariants

- **Do not break** `GET /health` response shape (root health must remain `{"status":"ok"}`).
- **Do not change** existing successful response schemas for shipped endpoints.
- Error responses are standardized; if you document an error body, use `backend/docs/ERROR_MODEL.md`.

## Related docs

- `backend/docs/ONBOARDING.md`
- `backend/docs/ARCHITECTURE.md`
- `backend/docs/ERROR_MODEL.md`
- `backend/docs/RATE_LIMITING.md`
- `backend/docs/AUTH_MODEL.md`
- `backend/docs/PROD_HARDENING.md`


