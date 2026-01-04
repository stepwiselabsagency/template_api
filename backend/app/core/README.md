## `app.core` — platform backbone

`app/core/` is the **cross-cutting infrastructure layer** for the FastAPI service. It owns:

- **Configuration** (Pydantic settings, `.env` loading, safe logging)
- **Central logging** (structured JSON/text logs, request correlation)
- **Middleware** (request id, request logging, and future global middleware)
- **App factory** (`create_app()` builds the FastAPI app consistently)

Business logic and feature routers should live outside `core/` (e.g. `app/api/`).

---

## Settings (`config.py`)

### Where to add a new setting

Add fields to `Settings` in `app/core/config.py` and give them:

- A **type**
- A **default** (when safe)
- A clear, **UPPERCASE** name (matches env var convention)

Access settings via:

- `get_settings()` (cached via `functools.lru_cache`)

### Environment variable naming rules

- Settings use **UPPERCASE** field names (`LOG_LEVEL`, `DATABASE_URL`, …).
- `ENV` also accepts `APP_ENV` for compatibility (via alias choices).

### Safe logging / redaction

Never log raw settings directly.

- Use `Settings.model_dump_safe()` which redacts embedded secrets in:
  - `DATABASE_URL`
  - `REDIS_URL`

---

## Logging (`logging.py`)

### How JSON logging works

`configure_logging(settings)` configures the **root logger** once during app creation.

- When `LOG_JSON=true`, logs are formatted as JSON using a custom formatter.
- When `LOG_JSON=false`, logs are formatted as readable text.

Every log line includes (when available):

- `timestamp`
- `level`
- `message`
- `logger`
- `request_id`

### How `request_id` is injected into logs

`request_id` is stored in a `contextvars.ContextVar`, so it automatically flows through async
code within the same request.

`RequestIdFilter` attaches `request_id` to every log record.

---

## Middleware stack (`middleware.py`)

### Order and why it matters

Middleware is installed in `app/core/app_factory.py`.

Important Starlette behavior:

- Middleware is applied in **reverse** order of `app.add_middleware(...)` calls.

The effective order (outermost → innermost) is:

- **CORS (outermost, optional)**: handles browser preflight and headers
- **Request ID**: sets `request_id` early and returns it in the response header
- **Telemetry**: records request metrics when enabled
- **Request logging**: logs a single summary line at request end
- **Rate limiting (inner, optional)**: applies only to `/api/v1/*` with health exemptions

This ensures:

- Every request gets a stable `request_id`
- The request summary log always has that `request_id`

### How to add a new middleware safely

- Keep middleware **small** and focused.
- Prefer `app.add_middleware(...)` in the app factory so ordering is explicit.
- If the middleware needs request correlation, read `request_id` from the logging context.
- If you change ordering or scope rules, also update `backend/docs/ARCHITECTURE.md`.

---

## App factory (`app_factory.py`)

`create_app()` is the single, canonical way to build the FastAPI app. It:

- Loads settings (`get_settings()`)
- Configures logging (`configure_logging(...)`)
- Creates the `FastAPI` instance
- Installs middleware in the correct order
- Includes routers (with `API_PREFIX`)
- Preserves `/health` at the root path

### Startup / shutdown going forward

Use the FastAPI lifespan in `create_app()` for startup/shutdown work.
Keep it fast, and avoid hard-failing when optional dependencies are down.

---

## Quick debugging tips

### Verify request id header locally

- Start the app (Docker or local Uvicorn)
- Call `/health` and confirm the response includes `X-Request-ID`

Example:

`curl -i http://localhost:8000/health`

### Verify request id appears in logs

- Make a request to any endpoint
- Look for `request_id` in the request summary log line (JSON) or `request_id=...` (text).


