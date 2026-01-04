# `backend/app/api/` — HTTP routing layer (legacy + versioned)

## Purpose

- Defines routers and route modules for the HTTP API surface.
- Separates **versioned** routes (`/api/v1`) from **legacy** (non-versioned) routes.

## Key modules/files

- **Legacy router**: `backend/app/api/router.py`
- **Legacy routes**: `backend/app/api/routes/`
  - Example: `backend/app/api/routes/auth.py` (`/auth/*`)
  - Example: `backend/app/api/routes/users.py` (`/users/*`)
- **v1 router**: `backend/app/api/v1/router.py`
- **v1 routes**: `backend/app/api/v1/routes/`
- **v1 schemas**: `backend/app/api/v1/schemas/`

## How it connects

- `backend/app/core/app_factory.py` mounts:
  - `v1_router` at `/api/v1`
  - legacy `router` at `settings.API_PREFIX` (default: empty string)

## Extension points

- **Add a new v1 route**:
  - Create `backend/app/api/v1/routes/<feature>.py` with `router = APIRouter(...)`
  - Include it in `backend/app/api/v1/router.py`
- **Add a new legacy route**:
  - Create `backend/app/api/routes/<feature>.py`
  - Include it in `backend/app/api/router.py`
- **Add a new API version**:
  - Create `backend/app/api/v2/` and include it from `backend/app/core/app_factory.py`

## Pitfalls / invariants

- **Stable paths**: do not change existing prefixes (`/api/v1`, `/auth`, etc.) for shipped endpoints.
- **Error bodies**: errors are normalized to the standard envelope; document them via `backend/docs/ERROR_MODEL.md`.

## Related docs

- `backend/docs/ARCHITECTURE.md`
- `backend/app/api/v1/README.md`
- `backend/docs/ERROR_MODEL.md`


