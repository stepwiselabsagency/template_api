# `backend/app/` — FastAPI application package

## Purpose

- Contains the runnable FastAPI application, organized into **core platform** and **feature API** modules.

## Key modules/files

- **Entrypoint**: `backend/app/main.py` (exports `app`)
- **App factory (wiring)**: `backend/app/core/app_factory.py`
- **Core platform**: `backend/app/core/`
- **API routes**:
  - **v1**: `backend/app/api/v1/` (mounted at `/api/v1`)
  - **legacy**: `backend/app/api/routes/` (mounted at `settings.API_PREFIX`, default: empty)
- **Auth**: `backend/app/auth/`
- **DB layer**: `backend/app/db/`
- **Models**: `backend/app/models/`
- **Repositories**: `backend/app/repositories/`

## How it connects

- `backend/app/main.py` is imported by the ASGI server (Uvicorn/Gunicorn) and calls `create_app()`.
- `backend/app/core/app_factory.py` wires routers, middleware, exception handlers, and hardening hooks.

## Extension points

- Add a new v1 route: create `backend/app/api/v1/routes/<feature>.py` and include it from `backend/app/api/v1/router.py`.
- Add a new dependency: add a function and use it via `Depends(...)` in route handlers.
- Add global middleware: implement in `backend/app/core/` and register in `backend/app/core/app_factory.py`.

## Pitfalls / invariants

- Keep modules small; avoid “god modules” in `core/` or `api/`.
- Don’t change the `/api/v1` mount prefix for existing routes.
- Don’t bypass the standard error model (see `backend/docs/ERROR_MODEL.md`).

## Related docs

- `backend/docs/ARCHITECTURE.md`
- `backend/docs/ONBOARDING.md`


