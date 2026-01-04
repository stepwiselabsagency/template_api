# `backend/app/repositories/` — Data access (repository pattern)

## Purpose

- Encapsulates database access behind small, testable classes.
- Keeps route handlers thin and avoids scattering SQLAlchemy queries across the routing layer.

## Key modules/files

- **Base repository helpers**: `backend/app/repositories/base.py`
- **User repository**: `backend/app/repositories/user_repository.py`

## How it connects

- Route handlers obtain a `Session` via `Depends(get_db)` (`backend/app/db/session.py`).
- Repositories are instantiated inside handlers or services:
  - `repo = UserRepository(db)`

## Extension points

- Add a new repository: `backend/app/repositories/<entity>_repository.py`
- Add a new query method: keep methods small and explicit; return ORM models or simple DTOs.

## Pitfalls / invariants

- Keep repositories synchronous (current code uses standard SQLAlchemy sessions).
- Avoid committing in multiple layers; follow the template convention (repository methods that mutate call `commit()`).

## Related docs

- `backend/app/db/README.md`
- `backend/docs/ARCHITECTURE.md`


