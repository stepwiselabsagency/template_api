# `backend/app/models/` — ORM models (SQLAlchemy)

## Purpose

- Defines SQLAlchemy ORM models for persistence.

## Key modules/files

- **User model**: `backend/app/models/user.py`
- **Model imports for Alembic**: `backend/app/models/__init__.py`

## How it connects

- Repositories in `backend/app/repositories/` query these models via a SQLAlchemy `Session`.
- Alembic autogenerate discovers models by importing `backend/app/models/__init__.py` from `backend/alembic/env.py`.

## Extension points

- Add a new model:
  - Create `backend/app/models/<model>.py`
  - Import it from `backend/app/models/__init__.py` so Alembic can see it
  - Generate migration: `make db-revision msg="add <model>"`

## Pitfalls / invariants

- If a model is not imported by `backend/app/models/__init__.py`, Alembic autogenerate may miss it.
- Keep model modules small (one model per file is a good default).

## Related docs

- `backend/app/db/README.md`
- `backend/docs/ONBOARDING.md`


