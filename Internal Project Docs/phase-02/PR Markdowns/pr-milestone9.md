# PR Title
`docs: phase-01 baseline lock + inventory (milestone 09, no behavior change)`

## Description
This PR implements **Milestone 09: Baseline Lock + Inventory** for Phase 02. It creates a locked, explicit “Phase 01 truth” snapshot (endpoints, invariants, env toggles, scripts, CI/test facts) and a repo inventory so Phase 02 cleanup/restructure can proceed safely with **zero runtime behavior changes**.

Key non-negotiables preserved:
- No runtime code changes (docs + Makefile only).
- Existing endpoints and successful response schemas remain unchanged.
- `/health` returns exactly `{"status":"ok"}` and responses include `X-Request-ID` (baseline invariants are documented, not changed).
- Standardized error envelope behavior remains unchanged.

---

## Changes

### Phase 01 baseline truth doc
Added `backend/docs/PHASE1_BASELINE.md` as the **LLM-friendly** “source of truth” for Phase 01:
- **Runtime entrypoint + stack**:
  - ASGI export: `backend/app/main.py` (`app = create_app()`)
  - Docker command: `uvicorn app.main:app ...` (from `Dockerfile`)
  - Compose services/versions: Postgres + Redis + app (from `docker-compose.yml`)
- **Complete endpoint inventory (derived from code/tests)**:
  - `/health`
  - `/api/v1/health/live`
  - `/api/v1/health/ready`
  - `/auth/login`, `/auth/me`
  - `/api/v1/users`, `/api/v1/users/me`, `/api/v1/users/{id}`
  - legacy `/users`, `/users/{id}`
- **Contractual invariants (derived from middleware/tests)**:
  - `/health` exact response body contract
  - `X-Request-ID` echo-or-generate behavior
  - Standard error envelope shape and where it applies (with 404/422 facts under `/api/v1`)
- **Configuration and env vars** grouped by area (DB/Redis/JWT/logging/hardening), with required vs optional behaviors based on settings/tests.
- **Testing & CI truth**:
  - pytest fixture isolation rules (hermetic env, settings cache clearing)
  - DB strategy (Postgres migrations in CI mode, SQLite fallback locally)
  - Note: no `.github/workflows/*` definitions are currently present in this repo baseline.
- **Operational scripts** under `scripts/` (only what exists) with example usage.

### Inventory doc for safe cleanup
Added `backend/docs/INVENTORY.md` to explain:
- Major directories/modules and why they exist
- Extension points vs “core”
- Deletion/cleanup **candidates** for Phase 02 (listed with risks, no changes proposed here)

### Makefile baseline verifier
Added a `verify-baseline` target to `Makefile`:
- Runs `make fmt`, `make lint`, `make test` (in that order)
- Then prints **guidance** for optional manual checks:
  - how to curl health endpoints if compose is already running
  - how to run verifier scripts (exact paths)
  - how to export Docker compose logs with the existing exporter script
- Does **not** require Docker to be running and does **not** start compose.

---

## Milestone Completion Criteria
- [x] `backend/docs/PHASE1_BASELINE.md` exists and is accurate (derived from code/tests/config/scripts).
- [x] `backend/docs/INVENTORY.md` exists and is accurate.
- [x] `make verify-baseline` exists and composes `fmt → lint → test`, then prints verifier guidance.
- [x] No runtime behavior changes.
- [x] CI remains green (no CI pipeline definitions changed/added in-repo).

---

## Notes / Design Decisions
- **Docs are explicit**: endpoints and invariants are described with exact paths and concrete behavior, backed by code/tests.
- **No Docker dependency** for `verify-baseline`: the target only prints optional manual verification steps.
- **Inventory includes candidates only**: it flags potentially deletable/duplicated areas for Phase 02 without changing anything.

---

## Validation Commands for Reviewer

```bash
make fmt
make lint
make test
make precommit
make verify-baseline
```


