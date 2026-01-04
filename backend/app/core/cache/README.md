# `backend/app/core/cache/` — Cache abstraction (optional)

## Purpose

- Provides a small cache interface with multiple backends:
  - **No-op** (default when disabled)
  - **In-memory** (used in tests when enabled but Redis isn’t)
  - **Redis** (intended for production)

## Key modules/files

- **Interface**: `backend/app/core/cache/interface.py`
- **Dependency**: `backend/app/core/cache/dependency.py` (`get_cache`)
- **Backends**:
  - `backend/app/core/cache/noop.py`
  - `backend/app/core/cache/in_memory.py`
  - `backend/app/core/cache/redis_cache.py`
- **Builder**: `backend/app/core/cache/__init__.py` (`build_cache`)

## How it connects

- `backend/app/core/app_factory.py` sets `app.state.cache = build_cache(settings)`.
- Route handlers can access it via `Depends(get_cache)`.
  - Example usage: `backend/app/api/v1/routes/users.py` caches `GET /api/v1/users/{id}`.

## Extension points

- Add a new backend implementation: create `backend/app/core/cache/<backend>.py` implementing the `Cache` interface.
- Select backend: update `build_cache(settings)` in `backend/app/core/cache/__init__.py`.

## Pitfalls / invariants

- Treat caching as **optional** and **best-effort** (fail open).
- Avoid caching request-specific values (example: `request_id`).

## Related docs

- `backend/docs/ARCHITECTURE.md`
- `backend/docs/PROD_HARDENING.md`


