# ARCHITECTURE — FastAPI Template

This document is the **architecture anchor** for humans and LLMs. It is intended to answer:

- “Where do requests enter and how do they flow?”
- “Where do I add a new endpoint/model/middleware?”
- “What invariants must not break?”

Start here if you’re new: `backend/docs/ONBOARDING.md`.

---

## High-level request flow (diagram)

```mermaid
flowchart LR
  Client[Client] -->|HTTP| App[FastAPI app]

  subgraph Middleware[Middleware (effective order)]
    CORS[CORS (optional)] --> RID[RequestIdMiddleware]
    RID --> TEL[TelemetryMiddleware]
    TEL --> RLOG[RequestLoggingMiddleware]
    RLOG --> RL[RateLimitMiddleware (only /api/v1/*)]
  end

  App --> Middleware --> Routes[Routing]

  Routes --> V1[/api/v1 router\nbackend/app/api/v1/]

  V1 --> Deps[Dependencies (Depends)]

  Deps --> Auth[get_current_user\nbackend/app/auth/dependencies.py]
  Deps --> DB[get_db\nbackend/app/db/session.py]
  Deps --> Cache[get_cache\nbackend/app/core/cache/dependency.py]

  DB --> Repo[Repositories\nbackend/app/repositories/]
  Repo --> ORM[ORM models\nbackend/app/models/]
  ORM --> Postgres[(Postgres)]

  Cache --> Redis[(Redis)]

  Routes --> Handlers[Exception handlers\nbackend/app/core/exception_handlers.py]
  Handlers -->|JSON error schema| Client
```

Notes:

- The middleware order above is the **effective** runtime order (see “Middleware ordering” below).
- The **standard error schema** is documented in `backend/docs/ERROR_MODEL.md`.

---

## Key invariants (do-not-break)

- **Root health endpoint**: `GET /health` must return exactly `{"status":"ok"}` (see `backend/app/core/app_factory.py`).
- **Stable successful response schemas**: do not change existing `response_model` outputs for shipped endpoints.
- **Versioned routing**: v1 routes remain mounted at `/api/v1` via `backend/app/api/v1/router.py`.
- **Error envelope**: handled errors should return the standard `{"error": ...}` schema (see `backend/docs/ERROR_MODEL.md`).
- **Rate limiting scope**: when enabled, applies only to `/api/v1/*` and excludes health endpoints (see `backend/docs/RATE_LIMITING.md`).

---

## App factory (creation path)

**File:** `backend/app/core/app_factory.py`

- **Canonical factory**: `create_app() -> FastAPI`
- Responsibilities:
  - Load settings: `backend/app/core/config.py:get_settings()`
  - Configure logging: `backend/app/core/logging.py:configure_logging(...)`
  - Initialize “hardening layer” state:
    - `app.state.telemetry = build_telemetry(settings)`
    - `app.state.cache = build_cache(settings)`
    - `app.state.rate_limiter = build_rate_limiter(settings)`
  - Register exception handlers: `backend/app/core/exception_handlers.py:register_exception_handlers(app)`
  - Install middleware (ordering is intentional; see below)
  - Include canonical public router (`/api/v1`)
  - Define `GET /health` at the root path

**Where to change app-wide wiring:**

- Add/remove middleware: `backend/app/core/app_factory.py`
- Add routers or change mount points: `backend/app/core/app_factory.py`

---

## Settings lifecycle (and caching)

**Files:**

- `backend/app/core/config.py` (`Settings`, `get_settings()`)

Facts (must remain true):

- `Settings` loads from environment variables and (for local dev) `.env`.
- `get_settings()` is cached via `functools.lru_cache`.

Extension points:

- Add a new setting: add a field to `Settings` in `backend/app/core/config.py`.
- Add redaction for safe logging: extend `Settings.model_dump_safe()`.

Pitfall:

- Because `get_settings()` is cached, changing environment variables at runtime will not affect an already-created app/process.

---

## Middleware ordering (and why it matters)

**Files:**

- Install order: `backend/app/core/app_factory.py`
- Implementations: `backend/app/core/middleware.py`, `backend/app/core/rate_limit/middleware.py`, `backend/app/core/telemetry_middleware.py`

Important Starlette behavior:

- Middleware is applied in **reverse order** of `app.add_middleware(...)` calls.

Current effective order (outermost → innermost):

- `CORSMiddleware` (only if configured)
- `RequestIdMiddleware` (sets `X-Request-ID` and contextvars early)
- `TelemetryMiddleware` (optional; samples and records request metrics)
- `RequestLoggingMiddleware` (single summary log line per request)
- `RateLimitMiddleware` (optional; only for `/api/v1/*`)

Where to change ordering:

- Edit the `app.add_middleware(...)` sequence in `backend/app/core/app_factory.py`.

---

## Routing strategy: canonical `/api/v1`

**Files:**

- v1 router: `backend/app/api/v1/router.py` (mounted at `/api/v1`)
- v1 route modules: `backend/app/api/v1/routes/`

Public API truth:

- **Canonical public API** is under `/api/v1/*`.
- `GET /health` exists as a minimal **infra convenience** liveness endpoint (not a parallel “legacy API surface”).

Extension points:

- Add `/api/v2`: create `backend/app/api/v2/` and include it from the app factory (do not mutate v1 paths).

---

## Dependency injection patterns

Common dependencies:

- **DB session**: `backend/app/db/session.py:get_db`
- **Current user**: `backend/app/auth/dependencies.py:get_current_user`
- **Cache**: `backend/app/core/cache/dependency.py:get_cache`

Pattern:

- Route handlers declare dependencies with `Depends(...)`.
- Dependencies should be small and composable (avoid complex side effects in dependencies).

---

## Data layer: models + repositories + DB sessions

**Files:**

- DB session: `backend/app/db/session.py`
- Base: `backend/app/db/base.py`
- ORM models: `backend/app/models/`
- Repositories: `backend/app/repositories/`
- Migrations: `backend/alembic/` + `backend/alembic.ini`

Invariants:

- Alembic autogenerate must be able to import models; ensure new models are imported by `backend/app/models/__init__.py`.

Extension points:

- Add a repository method: `backend/app/repositories/<repo>.py`
- Add a model: `backend/app/models/<model>.py` + import in `backend/app/models/__init__.py`

---

## Hardening layer components (what’s included)

This template includes a “hardening layer” that’s safe by default and mostly **optional**:

- **Standard error model**: `backend/app/core/errors.py`, `backend/app/core/exception_handlers.py`
- **Request id correlation**: `backend/app/core/middleware.py`, `backend/app/core/logging.py`
- **Rate limiting (optional)**: `backend/app/core/rate_limit/` (see `backend/docs/RATE_LIMITING.md`)
- **Cache (optional)**: `backend/app/core/cache/`
- **Telemetry hooks (optional)**: `backend/app/core/telemetry.py`, `backend/app/core/telemetry_middleware.py`

See also:

- `backend/docs/PROD_HARDENING.md`


