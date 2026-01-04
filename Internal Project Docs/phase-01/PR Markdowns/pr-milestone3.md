# PR Title
`feat: Persistence layer (SQLAlchemy + Alembic + repositories + users API)`

## Description
This PR implements Milestone 3: **Persistence Layer**. It adds a clean, reusable database architecture using **SQLAlchemy 2.x** + **Alembic** migrations, a base `User` model, a small repository pattern, and a minimal `/users` API to prove end-to-end DB integration — while keeping `/health` unchanged and preserving Docker entrypoints.

## Changes
- **Database module layout (`backend/app/db/`)**:
  - Added `base.py` (`Base`) for declarative models.
  - Added `session.py`:
    - `create_engine_from_settings(settings) -> Engine`
    - `SessionLocal` factory (SQLAlchemy 2.x style)
    - `get_db()` FastAPI dependency (session-per-request; closes in `finally`)
    - `get_engine()` accessor for scripts/tests
    - Engine creation uses `settings.DATABASE_URL` with sensible defaults (`pool_pre_ping=True`).
  - Added `README.md` documenting DB architecture, migration workflow, and common pitfalls.
- **Models (`backend/app/models/`)**:
  - Added `User` model (`users` table) with:
    - `id`: UUID primary key (Python `uuid.UUID` using SQLAlchemy `Uuid(as_uuid=True)`).
    - `email`: unique + indexed + not null.
    - `hashed_password`: not null.
    - `is_active`: boolean with default true.
    - `created_at` / `updated_at`: timezone-aware timestamps.
  - `app/models/__init__.py` imports all models so Alembic autogenerate can discover them.
- **Migrations (Alembic)**:
  - Added `backend/alembic.ini` + `backend/alembic/` environment.
  - `backend/alembic/env.py` loads `DATABASE_URL` from settings and targets `Base.metadata`.
  - Added initial migration `0001_create_users_table.py` creating the `users` table.
- **Repository layer (`backend/app/repositories/`)**:
  - Added `BaseRepository` (simple helpers: add/delete/commit/refresh).
  - Added `UserRepository`:
    - `get_by_id`, `get_by_email`, `create`, `list`, `set_active`.
- **Minimal users API (proves wiring)**:
  - Added `backend/app/api/routes/users.py`:
    - `POST /users` create user (uses placeholder `hash_password`)
    - `GET /users/{id}` fetch user
  - Updated `backend/app/api/router.py` to include the users router.
- **Security placeholder**:
  - Added `backend/app/core/security.py` with a clearly-marked placeholder `hash_password()` (NOT production-grade).
- **Makefile DB helpers**:
  - Added:
    - `make db-upgrade` → `alembic upgrade head` inside the app container
    - `make db-revision msg="..."` → autogenerate new migration
    - `make db-downgrade` → downgrade one revision
- **Tests**:
  - Added `backend/tests/test_persistence.py` to prove repository create+read works.
    - Prefers Postgres when `DATABASE_URL` is set (e.g. via docker-compose).
    - Falls back to SQLite for developer convenience when Postgres isn’t available.
  - Existing `/health` tests remain unchanged and still pass.

## Milestone Completion Criteria
- [x] Database stable: session lifecycle via `get_db()`; engine created from `DATABASE_URL`.
- [x] Migration system operational: Alembic config + initial migration for `users`.
- [x] Repository pattern implemented: `UserRepository` with required methods.
- [x] End-to-end proof: minimal `/users` API routes wired via dependency injection.
- [x] DB architecture documented: `backend/app/db/README.md`.
- [x] Tooling passes: `make fmt`, `make lint`, `make test`, `make precommit`.
- [x] `/health` remains unchanged (`/health` → `{"status":"ok"}`).

## Notes / Design Decisions
- **UUID strategy**: stored as a real UUID (`uuid.UUID`) using SQLAlchemy `Uuid(as_uuid=True)` for Postgres-native UUID support.
- **Email validation**: request schema uses `str` to avoid adding `email-validator` dependency to the base template; projects can switch to `EmailStr` if desired.
- **Password hashing**: `hash_password()` is a placeholder (SHA-256) and must be replaced before production use.
- **Migrations inside Docker**: recommended to run via `make db-upgrade` so the same runtime environment and `DATABASE_URL` is used.

## Related
- Milestone: Persistence Layer (SQLAlchemy + Alembic)
- Closes #3 (if applicable)

---

## Validation Commands for Reviewer
```bash
# 1. Setup environment
cp .env.example .env
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -e ".[dev]"

# 2. Run stack
make up
curl -i http://localhost:8000/health
# expect: HTTP 200, body {"status":"ok"}, and header X-Request-ID present

# 3. Run migrations
make db-upgrade

# 4. (Optional) sanity check users API
curl -i -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'
# expect: HTTP 201 and JSON body with id/email/is_active

# 5. Verify tooling
make fmt
make lint
make test
make precommit
```


