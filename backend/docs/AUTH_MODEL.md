## Overview

This template provides a minimal, security-minded authentication foundation:

- **Password hashing**: `passlib[bcrypt]`
- **Access tokens**: JWT (HS256) via `PyJWT`
- **Login endpoint**: `POST /api/v1/auth/login` (OAuth2 password flow)
- **Route protection**: `get_current_user()` dependency
- **Minimal RBAC**: `is_superuser` on `users`, mapped to the `"admin"` role

Related docs:

- `backend/docs/ONBOARDING.md`
- `backend/docs/ARCHITECTURE.md`
- `backend/docs/ERROR_MODEL.md` (standard error envelope + `WWW-Authenticate` preservation)
- `backend/docs/PROD_HARDENING.md`

Key source files:

- `backend/app/auth/password.py`
- `backend/app/auth/jwt.py`
- `backend/app/auth/service.py`
- `backend/app/auth/dependencies.py`
- `backend/app/api/v1/routes/auth.py`

## Password hashing

- **Algorithm**: bcrypt (via `passlib`)
- **Functions**:
  - `app.auth.password.hash_password(plain: str) -> str`
  - `app.auth.password.verify_password(plain: str, hashed: str) -> bool`

Notes:

- Password verification is constant-time (handled by passlib).
- **Never log** plaintext passwords or password hashes.

## JWT model

Settings (see `backend/app/core/config.py`):

- `JWT_SECRET_KEY` (**required outside `local`/`test`**)
- `JWT_ALGORITHM` (default `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` (default `60`)
- Optional hardening:
  - `JWT_ISSUER`
  - `JWT_AUDIENCE`

Claims used:

- `sub`: user id (UUID string)
- `iat`: issued-at (unix seconds)
- `exp`: expiration (unix seconds)
- `roles`: list of roles (minimal; `"admin"` when `is_superuser=true`)

Authorization header:

- `Authorization: Bearer <token>`

Token decoding validates:

- signature
- expiration (`exp`)
- issuer / audience if configured

Clock skew:

- Conservative `leeway=30s` is applied during decode.

## Login flow

Endpoint: `POST /api/v1/auth/login`

- Uses `OAuth2PasswordRequestForm`
  - Content-Type: `application/x-www-form-urlencoded`
  - Fields:
    - `username` (treated as email in this template)
    - `password`

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Example:

```bash
curl -i -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=pass123"
```

Failure modes:

- Invalid credentials: `401` with `WWW-Authenticate: Bearer`
- Inactive users: also `401` (does not leak user status)

## Protecting routes

Use:

- `app.auth.dependencies.get_current_user`

Example:

- `GET /api/v1/auth/me` is a minimal protected route implemented in
  `backend/app/api/v1/routes/auth.py`.

## Minimal RBAC

This template includes:

- DB field: `users.is_superuser` (boolean, default false)
- Role mapping:
  - `is_superuser=True` -> `"admin"`

Use:

- `app.auth.dependencies.require_roles(*roles)`

Example:

- `Depends(require_roles("admin"))`

## Security checklist (template defaults)

- **JWT secret**: set a strong `JWT_SECRET_KEY` in production.
- **Transport**: use HTTPS in real deployments (JWT bearer tokens must not travel over HTTP).
- **Token storage**: prefer HTTP-only secure cookies or secure platform storage; avoid localStorage when possible.
- **Rate limiting**: strongly recommended for `/api/v1/auth/login` (future milestone).
- **Refresh tokens**: not included yet (future milestone).

## How to extend

Common next steps:

- **Refresh tokens**: add a `refresh_token` model/table and a `/auth/refresh` route.
- **Revocation / blacklist**: store jti in Redis and deny on logout/revoke.
- **Multi-role RBAC**: add a `roles` table or many-to-many user-role mapping; include roles in token or query on demand.
- **Key rotation**: support multiple signing keys via `kid` header and a key store.


