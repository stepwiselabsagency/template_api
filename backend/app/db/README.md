# Database layer (`app/db`)

This template uses **SQLAlchemy 2.x** for ORM + sessions and **Alembic** for schema migrations.

## Folder layout

- `app/db/`
  - `base.py`: SQLAlchemy `Base` (declarative base). Alembic targets `Base.metadata`.
  - `session.py`: engine + session management + `get_db()` dependency.
- `app/models/`
  - ORM models (e.g. `User` in `user.py`).
  - `app/models/__init__.py` imports all models so Alembic autogenerate can “see” them.
- `app/repositories/`
  - Repository pattern wrapping DB access (e.g. `UserRepository`).
- `backend/alembic/`
  - Alembic migration environment (`env.py`) and revision files under `versions/`.
- `backend/alembic.ini`
  - Alembic config file. We pass it explicitly via `-c backend/alembic.ini`.

## How sessions work

Use `get_db()` as a FastAPI dependency:

- A new SQLAlchemy `Session` is created per request.
- The session is **closed** in a `finally` block.
- The engine is created lazily from `settings.DATABASE_URL` (no eager connections on import).

## How to add a new model + generate migrations

1) Create the model under `backend/app/models/` (example: `backend/app/models/widget.py`).
2) Import it from `backend/app/models/__init__.py` so Alembic can discover it.
3) Start infra:

```bash
make up
```

4) Generate a migration:

```bash
make db-revision msg="create widgets table"
```

5) Apply migrations:

```bash
make db-upgrade
```

## Repository pattern usage

Repositories take a `Session` and expose small, testable methods.

Example (API handler):

- `Depends(get_db)` yields a `Session`
- construct repository: `repo = UserRepository(db)`
- call methods like `repo.get_by_email(...)`, `repo.create(...)`

## Local dev workflow

1) Bring up stack:

```bash
make up
```

2) Run migrations:

```bash
make db-upgrade
```

3) Verify tables:

- Connect to Postgres (any client) using the same `DATABASE_URL`
- Confirm `users` exists

## Common pitfalls

- **Autogenerate doesn’t detect models**: ensure you imported the model from `app/models/__init__.py` (and Alembic `env.py` imports `app.models`).
- **Wrong `DATABASE_URL`**: Alembic uses `settings.DATABASE_URL` at runtime. Make sure your `.env`/compose env points to the DB you expect.
- **Running Alembic inside vs outside Docker**:
  - `make db-upgrade` runs Alembic **inside** the `app` container (recommended for consistency).
  - If you run Alembic locally, ensure your local env has the same `DATABASE_URL`.


