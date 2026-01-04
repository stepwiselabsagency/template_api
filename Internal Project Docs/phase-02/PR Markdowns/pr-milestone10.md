# PR Title
`feat: canonical /api/v1 API surface (milestone 10, remove legacy duplicates)`

## Description
This PR implements **Milestone 10 — API Surface Consolidation** for Phase 02 by establishing **one canonical public API surface** and removing duplicated/legacy route trees.

Final decisions (explicit, stable):
- **Canonical public surface**: `/api/v1/*` is the authoritative public API prefix.
- **Legacy routes policy**: **Option A — delete legacy duplicates** (no parallel legacy routing tree).
- **Auth path**: **Option A — move auth under v1**:
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`
- **`/health` policy**: **keep** `GET /health` as an explicit **infra convenience** liveness endpoint (not a second public API surface).

---

## Changes

### Canonical routing (single authority)
- `backend/app/core/app_factory.py`
  - mounts **only** the v1 router (`/api/v1`)
  - legacy router mount removed (no parallel route trees)
- `backend/app/api/v1/router.py`
  - includes `auth`, `health`, and `users` routers under `/api/v1`

### Auth moved under `/api/v1`
- Added v1 auth routes:
  - `backend/app/api/v1/routes/auth.py`
  - Exposes:
    - `POST /api/v1/auth/login`
    - `GET /api/v1/auth/me`
- Updated `OAuth2PasswordBearer` tokenUrl to canonical path:
  - `backend/app/auth/dependencies.py` now uses `tokenUrl="/api/v1/auth/login"`

### Legacy duplicates deleted
Removed legacy duplicate routing modules entirely:
- `backend/app/api/router.py` (deleted)
- `backend/app/api/routes/auth.py` (deleted)
- `backend/app/api/routes/users.py` (deleted)
- `backend/app/api/routes/__init__.py` (deleted)

### Docs updated to remove ambiguity
Updated documentation to clearly state the canonical surface and remove “legacy route tree” references:
- `backend/docs/ONBOARDING.md`
  - quickstart uses `GET /api/v1/health/live`
  - `/health` documented as infra convenience
- `backend/docs/ARCHITECTURE.md`
  - routing diagram + text updated to show **only** `/api/v1` as public router
- `backend/app/api/v1/README.md`
  - explicitly “canonical public API policy”
  - documents v1 auth endpoints and updated login flow
- `backend/docs/AUTH_MODEL.md`
  - updated to reference `/api/v1/auth/*` and v1 auth route module
- READMEs updated to match new structure:
  - `README.md`
  - `backend/app/README.md`
  - `backend/app/api/README.md`
  - `backend/app/auth/README.md`

### Tests + scripts updated to canonical endpoints
Updated all callers to use `/api/v1/auth/login` and `/api/v1/auth/me`:
- Tests:
  - `backend/tests/test_auth.py`
  - `backend/tests/fixtures/auth.py`
  - `backend/tests/integration/test_api_integration.py`
  - `backend/tests/test_v1_users.py`
  - `backend/tests/test_prod_hardening_cache.py`
- Black-box verifier:
  - `scripts/automated_tests/verify_prod_hardening.py` now logs in via `/api/v1/auth/login` and also checks `/api/v1/health/live`.

---

## Endpoints removed / renamed (explicit)

Removed legacy duplicates:
- `POST /auth/login` (removed)
- `GET /auth/me` (removed)
- `POST /users` (removed)
- `GET /users/{user_id}` (removed)

Canonical replacements:
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- Users remain only under `/api/v1/users/*`

Kept (infra convenience):
- `GET /health`

---

## Milestone Completion Criteria
- [x] `/api/v1` is the canonical public API surface (single router authority).
- [x] No duplicated user-create endpoints across routers (legacy `/users` removed).
- [x] Auth is canonical under `/api/v1/auth/*` and docs/tests/scripts reflect the new truth.
- [x] Docs updated to remove ambiguity.
- [x] Tests and verifier scripts updated and passing.

---

## Notes / Design Decisions
- **No parallel routing trees**: removing the legacy router eliminates ambiguity about “which endpoints are public”.
- **`/health` kept intentionally**: retained as a stable infra convenience liveness endpoint while `/api/v1/health/*` remains canonical for probes.
- **Auth under v1**: keeps the public surface cohesive and avoids cross-prefix coupling.

---

## Validation Commands for Reviewer

```bash
make fmt
make lint
make test
make precommit

# optional smoke (requires docker)
make up
make db-upgrade
curl -i http://localhost:8000/api/v1/health/live
curl -i http://localhost:8000/api/v1/health/ready
python scripts/automated_tests/verify_prod_hardening.py http://localhost:8000
```


