**Goal:** Restructure the codebase into clean, scalable module boundaries with strict dependency direction.

### Deliverables

Refactor to a layout that clearly separates:

- `core/` (cross-cutting platform)
- `features/` (domain modules)
- `infra/` (external integrations/backends)
- `db/` + migrations remain stable and predictable

**Recommended target (illustrative; exact naming is up to implementation but must be consistent):**

```text
backend/app/
|-- core/                 # settings, logging, middleware, errors, handlers
|-- infra/                # redis clients, cache backends, rate limit backends
|-- features/
|   |-- users/            # routes, schemas, service, repo (or repo in shared layer)
|   |-- auth/             # routes, schemas, jwt/password logic, deps
|-- db/                   # session/engine/Base
|-- models/               # SQLAlchemy models (or feature-owned models)
|-- main.py
```

**Refactoring rules:**

- `core` never imports `features`
- `features` may import `core` utilities
- `infra` has no knowledge of feature-level behavior

**Also deliver:**

- Update imports cleanly (no circular imports)
- Update docs and folder READMEs to reflect new structure
- Update `create_app()` wiring accordingly

### Acceptance Criteria

- Running the app works unchanged from user perspective (same canonical endpoints).
- No circular imports.
- All tests pass.
- Docs paths are correct and reflect new structure.

### Reviewer Validation

```bash
make fmt
make lint
make test
make precommit
```
