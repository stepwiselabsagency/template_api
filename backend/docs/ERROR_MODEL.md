# ERROR MODEL — Standard Error Response Contract

This document is the **single source of truth** for client-visible error responses.

Where it is implemented:

- Schema + helpers: `backend/app/core/errors.py`
- Exception handlers: `backend/app/core/exception_handlers.py`
- Request id propagation: `backend/app/core/middleware.py`, `backend/app/core/logging.py`

---

## Standard error schema

All handled errors return:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "request_id": "string|null",
    "details": "any|null"
  }
}
```

Field meanings:

- **`error.code`**: stable, machine-readable category (see mapping below).
- **`error.message`**: safe, human-readable summary.
- **`error.request_id`**: correlation id for logs; derived from `X-Request-ID` (or generated).
- **`error.details`**: optional structured details (used primarily for request validation).

Stability rules (do not break):

- Keep the **envelope shape** exactly `{"error": {...}}`.
- Keep `code` values stable for existing conditions.
- Preserve auth challenge headers (example: `WWW-Authenticate`) when present.

---

## Mapping rules (status → code)

Mapping is defined in `backend/app/core/errors.py:code_for_http_status(...)`.

- **422** → `validation_error`
  - **Request body/query validation**: `RequestValidationError` handler sets:
    - `message="Validation error"`
    - `details=[{"loc":[...],"msg":"...","type":"..."}]`
  - **Manual 422** via `HTTPException(..., detail="...")`:
    - `message` is the provided `detail` string
    - `details=null`
- **401** → `unauthorized`
  - `WWW-Authenticate: Bearer` is preserved when present.
- **403** → `forbidden`
- **404** → `not_found`
- **409** → `conflict`
  - May be raised as `HTTPException(409, detail="...")` or produced by `IntegrityError` handler.
- **429** → `rate_limited`
  - Emitted by `backend/app/core/rate_limit/middleware.py` when enabled.
- **500** → `internal_error`

Everything else maps to `http_error` (or `internal_error` for 5xx).

---

## Examples (curl + JSON)

### 401 Unauthorized (missing token)

```bash
curl -i http://localhost:8000/api/v1/users/me
```

Example response:

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Not authenticated",
    "request_id": "…",
    "details": null
  }
}
```

Note: the response includes `WWW-Authenticate: Bearer`.

---

### 422 Validation error (request validation)

```bash
curl -i -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{}'
```

Example response:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Validation error",
    "request_id": "…",
    "details": [
      {"loc":["body","email"],"msg":"Field required","type":"missing"},
      {"loc":["body","password"],"msg":"Field required","type":"missing"}
    ]
  }
}
```

---

### 422 Validation error (manual 422)

The template also raises 422 for a simple email sanity check (without the full validation details list).

```bash
curl -i -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"not-an-email","password":"pass123"}'
```

Example response:

```json
{
  "error": {
    "code": "validation_error",
    "message": "invalid email",
    "request_id": "…",
    "details": null
  }
}
```

---

### 409 Conflict (duplicate email)

```bash
curl -i -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'
```

Example response:

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

---

### 429 Rate limited (when enabled)

Enable rate limiting (see `backend/docs/RATE_LIMITING.md`), then send repeated requests:

```bash
for i in $(seq 1 5); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/health/live; done
```

Example error body:

```json
{
  "error": {
    "code": "rate_limited",
    "message": "Too many requests",
    "request_id": "…",
    "details": null
  }
}
```

---

## How handlers generate this schema

**File:** `backend/app/core/exception_handlers.py`

- `RequestValidationError` → `error_response(code="validation_error", message="Validation error", details=[...])`
- `HTTPException` → status-derived `code` + safe string `message`
  - Important: non-string `detail` values are not exposed; message becomes `"HTTP error"`.
- `IntegrityError` (SQLAlchemy, if installed) → 409 `conflict` with `message="Conflict"`
- Catch-all `Exception` → 500 `internal_error` with `message="Internal server error"`

**Header preservation:**

- `HTTPException.headers` (e.g., `{"WWW-Authenticate":"Bearer"}`) is passed through unchanged.


