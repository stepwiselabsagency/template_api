# Phase 02 — Milestones (Cleanup + Restructure + Heavy Testing)

**Phase 02 goal:** Convert the Phase 01 template into a production-grade, heavily reusable API template by aggressively cleaning legacy baggage, restructuring for long-term extensibility, and building a high-confidence testing + verification system (pytest + black-box scripts + compose smoke).

**Key principle:** This phase is allowed to delete code, routes, and compatibility layers if they are not necessary for a clean template.

**How to use these milestones:** Each milestone is a self-contained PR with:

- strict scope
- clear deliverables
- explicit acceptance criteria
- reviewer validation commands

---

## Milestone 9 — Baseline Lock + Inventory (No Behavior Change)

**Goal:** Create a "known-good baseline" snapshot and an explicit inventory of what exists, so cleanup/restructure doesn't accidentally remove required functionality.

### Deliverables

- `backend/docs/PHASE1_BASELINE.md`
  - exact list of public endpoints currently supported
  - exact invariants (e.g., `/health` response, `X-Request-ID`, error envelope)
  - current settings/env var inventory (what exists, what is optional)
  - list of scripts and what they verify
- `backend/docs/INVENTORY.md`
  - "why does this file exist?" table for major modules
  - identifies transitional code (compat wrappers, duplicate routers, legacy endpoints)
  - identifies candidates for deletion (with rationale)
- Add a single `make verify-baseline` target that runs:
  - `make fmt`, `make lint`, `make test`
  - and prints guidance for scenario scripts (does not require docker)

### Acceptance Criteria

- No runtime behavior changes.
- CI remains unchanged and green.
- Inventory docs are precise and LLM-friendly (explicit paths, no ambiguity).

### Reviewer Validation

```bash
make fmt
make lint
make test
make precommit
```

---

## Milestone 10 — API Surface Consolidation (Delete Legacy/Redundant Routes)

**Goal:** Establish one canonical API surface and remove duplication.

### Decisions this milestone must finalize

- **Canonical public prefix:** `/api/v1` becomes the authoritative public API.
- **Legacy routes policy:**
  - Either delete them, OR keep only a minimal compatibility set (explicitly documented).
- **Auth path decision:**
  - Either move auth under `/api/v1/auth/*`, OR keep `/auth/*` but make it explicitly "public surface" and document why.
- The point is to remove ambiguity: "the way to call this API is X."

### Deliverables

- Remove duplicate/legacy endpoints that overlap with v1:
  - remove legacy `/users` routes if they duplicate `/api/v1/users`
- Decide what happens to:
  - `/health` (keep or remove)
  - `/auth/login`, `/auth/me` (keep or move to v1)
- Update router wiring so there is a single router authority (no "parallel worlds").
- Update docs to match the new truth:
  - `backend/docs/ARCHITECTURE.md`
  - `backend/docs/ONBOARDING.md`
  - `backend/app/api/v1/README.md` (or new canonical API doc)
- Update all tests to match the new API surface.
- Update black-box scripts (e.g., `verify_prod_hardening.py`) to use canonical endpoints.

### Acceptance Criteria

- There are no duplicated user-create endpoints in multiple route trees.
- The canonical API is explicit and consistent everywhere (docs/tests/scripts).
- All tests pass locally and in CI.

### Reviewer Validation

```bash
make fmt
make lint
make test
make precommit

# manual smoke (depending on decisions)
make up
curl -i http://localhost:8000/api/v1/health/live
curl -i http://localhost:8000/api/v1/health/ready
```

---

## Milestone 11 — Folder Restructure to Production-Grade Boundaries

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

---

## Milestone 12 — Middleware + Error Model Hardening (Order, Guarantees, Tests)

**Goal:** Make middleware ordering intentional and verified; make the error model "unbreakable".

### Deliverables

- Middleware ordering is:
  - explicitly defined in one place
  - documented in `backend/docs/ARCHITECTURE.md`
  - validated via tests (not just described)
- Add tests that guarantee:
  - `X-Request-ID` always present on success AND standardized errors
  - error envelope always includes `request_id`
  - 401 preserves `WWW-Authenticate: Bearer`
  - 404/422 return standardized envelope consistently across public API
- Clean up exception handler logic:
  - ensure safe details content (no stack traces, no secrets)
  - consistent code mapping rules

### Acceptance Criteria

- All "error invariants" are asserted in tests.
- Middleware order is both documented and tested.
- No behavior regressions for successful responses.

### Reviewer Validation

```bash
make test-unit
make test-integration
make test
```

---

## Milestone 13 — Upgrade Black-box Verification Scripts into a Formal Harness

**Goal:** Turn the existing Python scripts into a consistent verification framework that can run locally and in CI.

### Deliverables

- Create `scripts/verify/` as a stable home:
  - `scripts/verify/verify_prod_hardening.py` (moved/renamed if needed)
  - `scripts/verify/verify_api_contracts.py` (new)
  - shared helpers: `scripts/verify/_client.py`, `_assertions.py`, `_output.py`
- All verifiers:
  - accept `--base-url`
  - have `--verbose`
  - exit code 0 on pass, non-zero on failure
  - print a concise PASS/FAIL summary
- Scenarios to include:
  - health checks
  - user create → login → me flow
  - error envelope checks (404/422)
  - rate limit behavior when enabled
  - cache behavior when enabled (verify redis keys if running with redis)
- Update docs:
  - `backend/docs/ONBOARDING.md` includes "how to run verifiers"

### Acceptance Criteria

- Verifiers run against a live server and reliably fail on broken contracts.
- Verifiers are deterministic (no random flaky assertions).

### Reviewer Validation

```bash
# with running server
python scripts/verify/verify_api_contracts.py --base-url http://localhost:8000
python scripts/verify/verify_prod_hardening.py --base-url http://localhost:8000
```

---

## Milestone 14 — Docker Compose Smoke Testing (Bring-up → Migrate → Verify → Logs)

**Goal:** Provide a single repeatable "stack-level" smoke test that proves the template works as a real deployable service.

### Deliverables

- Add `scripts/compose_smoke/`:
  - `smoke.py` or `smoke.sh` orchestrator that:
    - runs `make up`
    - runs migrations
    - runs verifiers against `http://localhost:8000`
    - exports logs via `export_docker_logs_json.py`
    - optionally validates that logs contain:
      - JSON lines when enabled
      - `request_id` presence
      - telemetry log lines when telemetry mode is log
    - runs `make down` (even on failure)
- Promote log export utility into a "supported tool":
  - `scripts/docker_logs/export_docker_logs_json.py` must be documented and used by smoke flow
- Add Make targets:
  - `make smoke` (runs the full sequence)
  - `make smoke-up` / `make smoke-down` (optional)

### Acceptance Criteria

- `make smoke` succeeds on a fresh machine with Docker installed.
- If something is broken, `make smoke` fails with a clear error and exits non-zero.
- Smoke script always tears down stack reliably.

### Reviewer Validation

```bash
make smoke
```

---

## Milestone 15 — CI 강화: Add Contract Verification + Optional Smoke Job

**Goal:** CI must validate not only unit/integration tests but also contract verifiers.

### Deliverables

- Extend `.github/workflows/ci.yml`:
  - Add a job step to run verifiers either:
    - by starting the server inside CI and calling scripts against it, OR
    - by using docker compose (if acceptable for CI), OR
    - by running "TestClient mode" verifiers (only if verifiers support it)
- Optional: add a separate workflow:
  - `smoke.yml` running on schedule or on demand
  - runs docker compose smoke

### Acceptance Criteria

- Main CI remains fast and stable.
- Verifiers run in CI in a deterministic way.
- PRs cannot merge if API contracts or error envelope invariants break.

### Reviewer Validation

- Confirm CI shows verifier step(s) passing on PR.

---

## Milestone 16 — Documentation Truth Pass (Post-Restructure Alignment)

**Goal:** After deletions and restructure, docs must be perfectly aligned.

### Deliverables

- Update docs to match final Phase 02 truth:
  - `backend/docs/ONBOARDING.md`
  - `backend/docs/ARCHITECTURE.md`
  - `backend/docs/ERROR_MODEL.md`
  - `backend/docs/RATE_LIMITING.md`
  - `backend/docs/AUTH_MODEL.md`
- Ensure every major directory has a short README with:
  - purpose
  - key files
  - extension points
- Update root README "Start here" to reflect new canonical API and new Make targets (`smoke`, verifiers).

### Acceptance Criteria

- No doc references old paths/endpoints that were deleted.
- A new developer can follow onboarding without guessing.

### Reviewer Validation

```bash
# spot-check:
rg "old/path|legacy" -n backend/docs
make smoke
```

---

## Phase 02 Completion Criteria (Overall)

Phase 02 is complete when:

- The repo has a single canonical API surface
- Legacy duplication is removed
- Structure is clean, modular, and production-grade
- Tests are strong (unit + integration + contract verifiers + compose smoke)
- CI enforces both tests and API contracts
- Docs match reality exactly

