# `backend/app/api/` — HTTP routing layer (canonical v1)

## Purpose

- Defines routers and route modules for the HTTP API surface.
- Exposes the canonical, versioned public API under `/api/v1`.

## Key modules/files

- **v1 router**: `backend/app/api/v1/router.py`
- **v1 routes**: `backend/app/api/v1/routes/`
- **v1 schemas**: `backend/app/api/v1/schemas/`

## How it connects

- `backend/app/core/app_factory.py` mounts `v1_router` at `/api/v1`.

## Extension points

- **Add a new v1 route**:
  - Create `backend/app/api/v1/routes/<feature>.py` with `router = APIRouter(...)`
  - Include it in `backend/app/api/v1/router.py`
- **Add a new API version**:
  - Create `backend/app/api/v2/` and include it from `backend/app/core/app_factory.py`

## Pitfalls / invariants

- **Stable paths**: do not change existing prefixes (`/api/v1`, `/auth`, etc.) for shipped endpoints.
- **Error bodies**: errors are normalized to the standard envelope; document them via `backend/docs/ERROR_MODEL.md`.

## Related docs

- `backend/docs/ARCHITECTURE.md`
- `backend/app/api/v1/README.md`
- `backend/docs/ERROR_MODEL.md`


