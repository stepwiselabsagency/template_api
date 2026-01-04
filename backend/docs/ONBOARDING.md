# ONBOARDING — FastAPI Template (30-minute path)

## What is this template?

- **FastAPI service skeleton** with a clear separation between **core platform** and **feature API routes**.
- **Versioned API baseline** under **`/api/v1`** (plus **legacy/non-versioned** routes for compatibility).
- **Production-hardening hooks** (standard error model, request id, optional cache, optional rate limiting, optional telemetry).
- **Docker Compose + Make** workflow for consistent local dev and CI parity.

Related docs:
- `backend/docs/ARCHITECTURE.md`
- `backend/docs/ERROR_MODEL.md`
- `backend/docs/RATE_LIMITING.md`
- `backend/docs/AUTH_MODEL.md`
- `backend/docs/PROD_HARDENING.md`

---

## Prereqs

- **Python**: 3.10+
- **Docker**: Docker Desktop + Compose
- **Make**: required for `make up`, `make test`, `make lint`, and `make precommit`
- **Git**
- **Windows note**: use **Git Bash** (or WSL) for `make` targets that rely on a POSIX shell.

---

## 5-minute quickstart (Docker Compose)

From repo root:

```bash
cp .env.example .env
make up
curl http://localhost:8000/health
```

Expected response (must remain stable):

```json
{"status":"ok"}
```

Stop:

```bash
make down
```

---

## Local dev tooling (format/lint/test + pre-commit)

Create a venv and install dev deps:

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows (Git Bash)
source .venv/Scripts/activate

pip install -e ".[dev]"
```

Run the standard workflow (same commands CI uses):

```bash
make fmt
make lint
make test
make precommit
```

---

## Mental model (how requests flow)

**Request flow (simplified):**

- **Entry point**: `backend/app/main.py` creates the app via `backend/app/core/app_factory.py:create_app()`
- **Middleware**: request id → telemetry → request logging → rate limiting (see `backend/docs/ARCHITECTURE.md`)
- **Routing**:
  - **v1 routes**: `backend/app/api/v1/` mounted at `/api/v1`
  - **legacy routes**: `backend/app/api/routes/` mounted at `settings.API_PREFIX` (default: empty string)
- **Dependencies**:
  - DB session: `backend/app/db/session.py:get_db`
  - Auth: `backend/app/auth/dependencies.py:get_current_user`
  - Cache: `backend/app/core/cache/dependency.py:get_cache`
- **Data access**: repositories in `backend/app/repositories/` use SQLAlchemy sessions and ORM models in `backend/app/models/`
- **Errors**: all errors are normalized to a stable schema (see `backend/docs/ERROR_MODEL.md`)

**Where config lives:**

- `backend/app/core/config.py` defines `Settings` and `get_settings()` (cached via `lru_cache`)
- `.env` is loaded in local dev; tests default to a hermetic environment (see `backend/tests/README.md`)

---

## Common tasks (“where do I change X?”)

### Add an endpoint (v1)

- **Add route module**: `backend/app/api/v1/routes/<feature>.py`
- **Wire it into v1 router**: `backend/app/api/v1/router.py`
- **Add/adjust schemas**: `backend/app/api/v1/schemas/<feature>.py`
- **Add tests**: `backend/tests/test_v1_<feature>.py` or `backend/tests/integration/`

### Add an endpoint (legacy / non-versioned)

- **Add route module**: `backend/app/api/routes/<feature>.py`
- **Wire it into legacy router**: `backend/app/api/router.py`
- **Confirm mount**: `backend/app/core/app_factory.py` mounts `api_router` with `prefix=settings.API_PREFIX`

### Add a model + migration (SQLAlchemy + Alembic)

- **Add ORM model**: `backend/app/models/<model>.py`
- **Ensure Alembic discovery**: import the model in `backend/app/models/__init__.py`
- **Generate migration** (runs inside the app container):

```bash
make up
make db-revision msg="add widgets table"
make db-upgrade
```

### Add a dependency (FastAPI Depends)

- **DB**: add in `backend/app/db/session.py` (or create `backend/app/db/<module>.py` and re-export from `backend/app/db/__init__.py`)
- **Auth**: `backend/app/auth/dependencies.py`
- **Cache**: `backend/app/core/cache/dependency.py`

### Add middleware

- **Core middleware implementations**: `backend/app/core/middleware.py`
- **Install / order middleware**: `backend/app/core/app_factory.py`

Important: Starlette applies middleware in **reverse** order of `add_middleware(...)` calls (details in `backend/docs/ARCHITECTURE.md`).

### Add a test

- **Unit tests**: `backend/tests/unit/` (pure logic)
- **Integration tests**: `backend/tests/` and `backend/tests/integration/` (HTTP via `TestClient`)
- **Fixtures**: `backend/tests/fixtures/` and `backend/tests/conftest.py`

---

## How to run tests (unit vs integration)

All tests:

```bash
make test
```

Focused:

```bash
make test-unit
make test-integration
```

CI parity tip (run integration tests against Postgres):

```bash
DATABASE_URL="postgresql+psycopg://app:app@localhost:5432/app" make test
```

---

## Where to read next

- **Architecture**: `backend/docs/ARCHITECTURE.md`
- **Error model (client contract)**: `backend/docs/ERROR_MODEL.md`
- **Rate limiting**: `backend/docs/RATE_LIMITING.md`
- **Auth model**: `backend/docs/AUTH_MODEL.md`
- **Hardening overview**: `backend/docs/PROD_HARDENING.md`


