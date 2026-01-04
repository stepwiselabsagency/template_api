# PR Title
`feat: Core application architecture (settings, logging, middleware, app factory)`

## Description
This PR implements Milestone 2: **Core Application Architecture**. It introduces a clear `app/core/` backbone for configuration, centralized logging, request tracing, middleware ordering, and an app factory — while preserving `/health` behavior and keeping Docker/uvicorn entrypoints stable.

## Changes
- **Core Module Layout (`backend/app/core/`)**:
  - **Settings**: Added `config.py` using **pydantic-settings** (Pydantic v2 style) with `Settings`, `get_settings()` cache, and `model_dump_safe()` redaction.
  - **Logging**: Added `logging.py` with `configure_logging()` and JSON/text formatting; request correlation via `contextvars`.
  - **Middleware**: Added `middleware.py` with:
    - Request ID middleware (uses incoming `X-Request-ID` or generates UUID; always returns header)
    - Request logging middleware (one summary line per request + exception logging)
  - **App factory**: Added `app_factory.py` with `create_app()` that wires settings → logging → middleware → routers.
  - **Docs**: Added `README.md` explaining how to extend core safely.
- **Entrypoint stability**:
  - Updated `backend/app/main.py` to expose `app = create_app()` (Docker continues running `uvicorn app.main:app`).
  - Preserved `/health` exactly: same route (`/health`) and same response (`{"status":"ok"}`).
- **Dependencies**:
  - Added pinned runtime dependency: `pydantic-settings==2.6.1` in `pyproject.toml` (minimal addition required for Pydantic v2 settings).
- **Environment defaults**:
  - Added/updated `.env.example` to include new config keys (logging + request id) with sensible defaults.
- **Tests**:
  - Updated `backend/tests/test_health.py` to assert:
    - `/health` returns `{"status":"ok"}`
    - response includes `X-Request-ID`
    - incoming `X-Request-ID` is echoed back

## Milestone Completion Criteria
- [x] App boots with structured config (Pydantic settings + cached accessor).
- [x] Requests log with traceability (request_id stored via contextvars; returned via header).
- [x] Architecture is documented and understandable (`backend/app/core/README.md`).
- [x] `/health` remains unchanged (`/health` → `{"status":"ok"}`).
- [x] Tooling passes: `make fmt`, `make lint`, `make test`, `make precommit`.

## Related
- Milestone: Core Application Architecture
- Closes #2 (if applicable)

---

## Validation Commands for Reviewer
```bash
# 1. Setup environment
cp .env.example .env
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -e ".[dev]"

# 2. Run stack
make up
curl -i http://localhost:8000/health
# expect: HTTP 200, body {"status":"ok"}, and header X-Request-ID present

# 3. Verify tooling
make fmt
make lint
make test
make precommit
```


