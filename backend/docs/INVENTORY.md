# INVENTORY — Phase 01 modules, purpose, and deletion candidates

This document inventories what exists in Phase 01 so Phase 02 restructuring can be done safely. It explains **why major modules exist**, highlights **extension points vs core**, and lists **candidates** that may be deletable later (without proposing changes here).

---

## High-level map (major directories)

```text
repo-root/
|-- backend/
|   |-- app/                  # FastAPI application package
|   |-- alembic/              # migrations
|   |-- tests/                # unit + integration tests
|   `-- docs/                 # template docs (architecture/contracts)
|-- scripts/                  # repo utilities (non-runtime)
|-- Internal Project Docs/    # milestone plans + summaries (project docs)
|-- docker-compose.yml        # local infra (postgres + redis + app)
|-- Dockerfile                # container build + uvicorn command
|-- Makefile                  # fmt/lint/test + compose helpers
|-- env.example               # example env vars
`-- pyproject.toml            # deps + tooling configuration
```

---

## Module inventory (path → responsibility → why it exists)

Structured inventory (Phase 01 truth; “Deletion candidates?” is informational only):

### Core application + platform

- **Path**: `backend/app/`
  - **Responsibility**: FastAPI application code (routing, auth, DB, core middleware/handlers).
  - **Key files**:
    - `backend/app/main.py` (exports ASGI `app`)
    - `backend/app/core/app_factory.py` (wiring + `/health`)
    - `backend/app/api/` (routers)
  - **Why it exists**: Primary service package (installed via `pyproject.toml` `package-dir = "backend"`).
  - **Deletion candidates?**: No
  - **Notes / Risks if removed**: Entire API disappears.

- **Path**: `backend/app/core/`
  - **Responsibility**: Cross-cutting “platform” layer (settings, middleware, logging, error model, optional hardening).
  - **Key files**:
    - `backend/app/core/config.py`
    - `backend/app/core/exception_handlers.py`
    - `backend/app/core/middleware.py`
  - **Why it exists**: Centralizes invariants (request id, error envelope, middleware ordering) and optional hardening features.
  - **Deletion candidates?**: No
  - **Notes / Risks if removed**: Breaks contractual invariants (`/health` header behavior, standard errors, rate limit scope).

- **Path**: `backend/app/api/`
  - **Responsibility**: HTTP routing layer (canonical v1 public API under `/api/v1`).
  - **Key files**:
    - `backend/app/api/v1/router.py`
    - `backend/app/api/v1/routes/auth.py`
    - `backend/app/api/v1/routes/users.py`
  - **Why it exists**: Keeps route modules small and separated from core wiring.
  - **Deletion candidates?**: No
  - **Notes / Risks if removed**: Removing v1 routes breaks the canonical API surface.

- **Path**: `backend/app/api/v1/`
  - **Responsibility**: Versioned public API surface under `/api/v1`.
  - **Key files**:
    - `backend/app/api/v1/router.py` (mount prefix `/api/v1`)
    - `backend/app/api/v1/routes/health.py`
    - `backend/app/api/v1/routes/users.py`
  - **Why it exists**: Provides a stable versioned contract surface; allows future `/api/v2` without breaking v1.
  - **Deletion candidates?**: No
  - **Notes / Risks if removed**: Breaks v1 contract and tests; rate limiting scope is tied to `/api/v1/*`.

- **Path**: `backend/app/auth/`
  - **Responsibility**: Authentication primitives (password hashing, JWT issuance/validation, auth dependencies).
  - **Key files**:
    - `backend/app/auth/jwt.py`
    - `backend/app/auth/dependencies.py`
    - `backend/app/auth/service.py`
  - **Why it exists**: Keeps auth logic reusable across routes; enforces consistent `401` behavior.
  - **Deletion candidates?**: No
  - **Notes / Risks if removed**: Breaks protected endpoints (`/api/v1/auth/me`, `/api/v1/users/me`, `/api/v1/users/{id}`).

- **Path**: `backend/app/db/`
  - **Responsibility**: SQLAlchemy engine/session wiring + Base.
  - **Key files**:
    - `backend/app/db/session.py` (`get_db`, engine creation)
    - `backend/app/db/base.py`
  - **Why it exists**: Centralizes DB session behavior and keeps imports from requiring a configured DB.
  - **Deletion candidates?**: No
  - **Notes / Risks if removed**: All DB-backed endpoints and migrations break.

- **Path**: `backend/app/models/` and `backend/app/repositories/`
  - **Responsibility**: ORM models and DB access logic.
  - **Key files**:
    - `backend/app/models/user.py`
    - `backend/app/repositories/user_repository.py`
  - **Why it exists**: Separates DB persistence concerns from request handlers.
  - **Deletion candidates?**: No
  - **Notes / Risks if removed**: Breaks user endpoints and auth user lookup.

### Migrations

- **Path**: `backend/alembic/` and `backend/alembic.ini`
  - **Responsibility**: Alembic migrations for schema evolution.
  - **Key files**:
    - `backend/alembic/env.py`
    - `backend/alembic/versions/0001_create_users_table.py`
  - **Why it exists**: Provides production-grade schema migration path (tests also use it in Postgres mode).
  - **Deletion candidates?**: No
  - **Notes / Risks if removed**: CI/Postgres test mode and production DB upgrades break.

### Tests

- **Path**: `backend/tests/`
  - **Responsibility**: Unit + integration tests; locks API invariants (health, request id, error model, endpoints).
  - **Key files**:
    - `backend/tests/test_health.py` (root health contract)
    - `backend/tests/integration/test_api_integration.py` (end-to-end flow + error envelope)
    - `backend/tests/fixtures/` (env + DB isolation)
  - **Why it exists**: Defines baseline behavior and prevents accidental runtime behavior changes.
  - **Deletion candidates?**: No
  - **Notes / Risks if removed**: Baseline safety net disappears; Phase 02 becomes high risk.

### Docs

- **Path**: `backend/docs/`
  - **Responsibility**: Human/LLM-readable architecture + contracts for the template.
  - **Key files**:
    - `backend/docs/ARCHITECTURE.md`
    - `backend/docs/ERROR_MODEL.md`
    - `backend/docs/AUTH_MODEL.md`
  - **Why it exists**: Captures invariants and extension points; avoids “tribal knowledge”.
  - **Deletion candidates?**: Maybe (select docs)
  - **Notes / Risks if removed**: Higher onboarding cost; higher chance of contract breaks.

### Repo tooling + local stack

- **Path**: `Makefile`
  - **Responsibility**: Standard dev commands (`fmt`, `lint`, `test`, `precommit`) + compose helpers.
  - **Key files**: `Makefile`
  - **Why it exists**: Repeatability and CI parity for contributors.
  - **Deletion candidates?**: Maybe (if replaced by another task runner)
  - **Notes / Risks if removed**: Harder onboarding; docs reference `make` commands.

- **Path**: `docker-compose.yml` and `Dockerfile`
  - **Responsibility**: Local stack + container build.
  - **Key files**:
    - `docker-compose.yml` (postgres/redis/app)
    - `Dockerfile` (uvicorn command)
  - **Why it exists**: Fast local bring-up and consistent runtime packaging.
  - **Deletion candidates?**: Maybe (if local stack strategy changes)
  - **Notes / Risks if removed**: Losing easy Postgres/Redis parity; scripts that read compose logs become less useful.

- **Path**: `scripts/`
  - **Responsibility**: Non-runtime utilities for verification and debugging.
  - **Key files**:
    - `scripts/automated_tests/verify_prod_hardening.py`
    - `scripts/docker_logs/export_docker_logs_json.py`
  - **Why it exists**: Provides baseline verifiers and operational helpers without affecting runtime code.
  - **Deletion candidates?**: Maybe (individual scripts)
  - **Notes / Risks if removed**: Lose easy “smoke/verification” tooling; fewer guardrails during changes.

### Project docs (non-runtime)

- **Path**: `Internal Project Docs/`
  - **Responsibility**: Project planning docs (milestones, PR markdowns, phase summaries).
  - **Key files**:
    - `Internal Project Docs/phase-01/phase-01-summary.md`
    - `Internal Project Docs/phase-01/plan/milestones.md`
  - **Why it exists**: Tracks milestone intent and decisions outside runtime code.
  - **Deletion candidates?**: Maybe (depending on repo policy)
  - **Notes / Risks if removed**: Loses historical context (but does not affect runtime).

---

## Deletion/cleanup candidates (Phase 02) — candidates only

These are **candidates** to evaluate later; do not remove in Phase 01 baseline.

- **Legacy route tree removal**
  - Candidate: already completed as part of Phase 02 API consolidation (canonical `/api/v1` only). Reintroducing a parallel legacy route tree is discouraged.

- **Some docs may be redundant with baseline docs**
  - Candidate: later deduplicate overlapping explanations across `backend/docs/*` once Phase 02 structure is finalized.
  - Risk: removing docs can unintentionally remove contract documentation used by contributors/LLMs.

- **Example artifacts at repo root (`app-logs-200.*`)**
  - Candidate: treat as sample outputs; consider moving to a dedicated examples/fixtures directory if they are meant to be kept.
  - Risk: none for runtime; but can clutter repo root.


