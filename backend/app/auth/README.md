# `backend/app/auth/` — Authentication & authorization

## Purpose

- Implements password hashing, JWT issuance/verification, and FastAPI dependencies for route protection.

## Key modules/files

- **Password hashing**: `backend/app/auth/password.py`
- **JWT encode/decode**: `backend/app/auth/jwt.py`
- **Auth service** (verify + issue token): `backend/app/auth/service.py`
- **Dependencies** (`get_current_user`, `require_roles`): `backend/app/auth/dependencies.py`

## How it connects

- Login endpoint is a **legacy route**:
  - `backend/app/api/routes/auth.py` exposes `POST /auth/login` and `GET /auth/me`
- Protected v1 routes depend on:
  - `Depends(get_current_user)` from `backend/app/auth/dependencies.py`

## Extension points

- **Add roles/RBAC**:
  - Token roles are currently emitted in `backend/app/auth/service.py` via `"roles": [...]`
  - Route-side checks live in `backend/app/auth/dependencies.py:require_roles(...)`
- **Change JWT claims**:
  - Edit `backend/app/auth/jwt.py:create_access_token(...)` and keep decode validations aligned.

## Pitfalls / invariants

- Auth failures should preserve `WWW-Authenticate: Bearer` when raised via `HTTPException(..., headers=...)`.
- Do not log plaintext passwords.

## Related docs

- `backend/docs/AUTH_MODEL.md`
- `backend/docs/ERROR_MODEL.md`
- `backend/docs/ONBOARDING.md`


