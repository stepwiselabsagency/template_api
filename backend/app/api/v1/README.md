# API v1 (`/api/v1`)

This directory defines the **versioned public API surface** for the template.

**Canonical public API policy:** `/api/v1` is the authoritative public API surface.

## Why versioned routing?

We expose new public endpoints under **`/api/v1`** so future breaking changes can be shipped under **`/api/v2`** without breaking existing clients.

- **v1**: `backend/app/api/v1/` (mounted at `/api/v1`)
- **v2 (future)**: add `backend/app/api/v2/` and mount a new `v2_router = APIRouter(prefix="/api/v2")`

## Router layout

- `backend/app/api/v1/router.py`
  - Defines `v1_router = APIRouter(prefix="/api/v1")`
  - Includes:
    - `auth_router` (`/auth`)
    - `health_router` (`/health`)
    - `users_router` (`/users`)
- `backend/app/api/v1/routes/`
  - `auth.py`: login + current user
  - `health.py`: liveness/readiness
  - `users.py`: user endpoints
- `backend/app/api/v1/schemas/`
  - `users.py`: Pydantic request/response models for user routes

### Adding a new route module

1. Create a new module in `backend/app/api/v1/routes/`, e.g. `items.py`:
   - define `router = APIRouter(prefix="/items", tags=["items"])`
2. Include it in `backend/app/api/v1/router.py`:
   - `v1_router.include_router(items_router)`

Keep route modules small and keep shared models in `schemas/` to avoid circular imports.

## Endpoints

### `POST /api/v1/auth/login`

Issue an access token (OAuth2 password form).

Request:

- Content-Type: `application/x-www-form-urlencoded`
- Fields:
  - `username` (treated as email in this template)
  - `password`

Response (200):

```json
{"access_token":"<jwt>","token_type":"bearer","expires_in":3600}
```

Example:

```bash
curl -i -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=pass123"
```

### `GET /api/v1/auth/me`

Return the current user (auth required).

Response (200):

```json
{"id":"<uuid>","email":"user@example.com","is_active":true,"is_superuser":false}
```

### `GET /api/v1/health/live`

Liveness probe (process running). Does **not** depend on DB/Redis.

Response:

```json
{"status":"ok"}
```

### `GET /api/v1/health/ready`

Readiness probe (dependencies available).

- Checks **database** connectivity (required)
- Checks **Redis** connectivity when `REDIS_URL` is configured

Ready response (200):

```json
{"status":"ok","checks":{"db":"ok","redis":"ok"}}
```

Not-ready response (503):

```json
{"status":"error","checks":{"db":"error","redis":"ok"}}
```

### `POST /api/v1/users`

Create a user.

Request:

```json
{"email":"user@example.com","password":"pass123"}
```

Responses:

- `201 Created`:

```json
{"id":"<uuid>","email":"user@example.com","is_active":true,"is_superuser":false}
```

- `409 Conflict` (email exists):

```json
{
  "error": {
    "code": "conflict",
    "message": "email already exists",
    "request_id": "…",
    "details": null
  }
}
```

### `GET /api/v1/users/me`

Return the current user (auth required).

Response (200):

```json
{"id":"<uuid>","email":"user@example.com","is_active":true,"is_superuser":false}
```

### `GET /api/v1/users/{id}`

Get a user by id (auth required).

Authorization rule:

- Allowed if requesting **own user**
- Allowed if current user is **superuser**
- Otherwise `403 Forbidden`

Response (200):

```json
{"id":"<uuid>","email":"user@example.com","is_active":true,"is_superuser":false}
```

## Auth usage (token)

Get a token from:

- `POST /api/v1/auth/login` (OAuth2 password form)

Then call protected endpoints with:

`Authorization: Bearer <token>`

```bash
curl -i http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <token>"
```

## Common pitfalls

- **Request tracing**: responses include `X-Request-ID` (incoming `X-Request-ID` is preserved).
- **Readiness vs liveness**:
  - `/api/v1/health/live` should be used for liveness probes.
  - `/api/v1/health/ready` should be used for readiness probes and may return `503`.
- **DB readiness & migrations**: if the DB is up but migrations haven’t been applied, your app may still start but features can fail—run Alembic migrations in your deployment pipeline.
- **HTTP status meanings**:
  - `401`: missing/invalid token
  - `403`: authenticated but not allowed
  - `409`: conflict (email already exists)

Related docs:

- `backend/docs/ERROR_MODEL.md` (standard error envelope)
- `backend/docs/ARCHITECTURE.md`


