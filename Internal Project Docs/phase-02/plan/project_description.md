# Phase 02 — Project Description (Cleanup + Restructure + "Serious" Testing)

**Goal:** Turn the Phase 01 template into a production-grade, heavy-use API template by (1) removing legacy baggage and duplication, (2) enforcing a clean, extensible architecture with strict boundaries, and (3) building a high-confidence testing system (unit + integration + black-box + compose-level) so future feature phases can move fast without regressions.

This Phase 02 is not about adding new product features. It is about making the template elite for long-term reuse.

## 1) Phase 02 guiding principles

### 1.1 "Clean baseline" over backwards compatibility

Phase 01 intentionally preserved legacy endpoints/routers and compatibility while building milestone-by-milestone. Phase 02 flips that: we prioritize correctness, clarity, and maintainability over keeping old paths alive.

**Expected outcome:**

- Reduce redundant routes (especially duplicate "legacy vs v1" behavior).
- Remove any placeholder / transitional code that exists only because of milestone progression.

### 1.2 Production-first structure

Adopt a structure that:

- scales in complexity without becoming tangled
- keeps "core platform concerns" isolated (config/logging/errors/telemetry)
- keeps "domain features" modular (users/auth/…)
- makes dependency direction obvious and enforceable

### 1.3 Tests become the safety rail

Restructuring is only safe if we have:

- deterministic tests
- fast feedback loops
- realistic integration coverage
- black-box / scenario scripts for "hit the API many times" behavior
- compose-level smoke tests for infra + readiness + logging expectations

## 2) Phase 02 deliverables (what "done" looks like)

### 2.1 Architecture cleanup + consolidation

- A single, authoritative API surface (likely `/api/v1` only; legacy removed if not needed).
- No duplicate "user create" endpoints across routers.
- Clear "what is public API" and "what is internal".

### 2.2 Folder/module reorganization (extensible + maintainable)

A reorganized `backend` layout where:

- core concerns are stable and small
- features/domains are self-contained
- interfaces (protocols/ports) are clearly separated from implementations

All folder READMEs updated to reflect the new truth.

### 2.3 Strict error + middleware + lifecycle invariants

- Middleware ordering is intentional, documented, and validated by tests.
- Error envelope is the only error shape used across the public API surface (except explicitly exempted endpoints, if any).
- Request ID propagation is guaranteed and tested in multiple layers.

### 2.4 Test system upgraded to "serious production template" level

A complete testing stack that includes:

- **Unit tests** (pure business logic, fast, isolated)
- **Integration tests** (FastAPI + DB + Redis, realistic)
- **Black-box scenario tests** (hit running API repeatedly, validate headers/behavior)
- **Docker Compose smoke tests** (bring up stack, run migrations, run scenario scripts)

A "CI parity" workflow that runs locally exactly like GitHub Actions.

### 2.5 Verification scripts become first-class

The existing Python scripts (e.g., prod-hardening verifier, docker log exporter) become:

- documented,
- structured,
- runnable in CI and locally,
- and validated (with predictable outputs / exit codes).

## 3) Proposed technical approach (Phase 02 plan)

### 3.1 Consolidate routing and remove legacy duplication

**Intent:** A template should have exactly one canonical way to do things.

**Actions:**

- Decide the canonical API surface:
  - likely keep `/api/v1` as the only public API
  - remove or deprecate legacy `api/` routing if it duplicates v1
- Keep only what is necessary:
  - health endpoints: decide whether `/health` stays for infra convenience, or move everything under v1
  - auth endpoints: decide whether `/auth/*` should live under `/api/v1/auth/*` for consistency
- Update docs + scripts + tests accordingly.

**Deliverable:**

- A single routing tree with a single router entrypoint and predictable module structure.

### 3.2 "Production-ready module boundaries" restructure

**Intent:** Make extension easy without accidental coupling.

**Recommended target shape (conceptual, not final):**

- `app/core/` = cross-cutting platform concerns only (config/logging/errors/middleware)
- `app/features/<feature_name>/` = self-contained feature modules
  - `routes.py` (or `api.py`)
  - `schemas.py`
  - `service.py` (domain logic)
  - `repo.py` (data access)
  - `models.py` (or shared models remain in `app/models/`)
- `app/infra/` = integrations (db, redis, cache backends, rate limit backend implementations)
- `app/main.py` stays a thin entrypoint calling `create_app()`

**Actions:**

- Move code into stable, predictable places.
- Remove "transitional" wrappers that exist only because of earlier milestones, unless they provide real value.
- Ensure imports follow one direction:
  - routes → deps/service → repo → infra/db
  - core does not import features
  - features can import core utilities, but core never imports features

**Deliverables:**

- a clean "map of the system"
- updated folder READMEs reflecting the new structure
- docs corrected to match new paths

### 3.3 Clarify "hardening layer" and make it truly plug-and-play

**Intent:** optional modules should be easy to enable and hard to misuse.

**Actions:**

- Ensure rate limiting / cache / telemetry are:
  - behind small protocols (already true)
  - configured via settings
  - attached to `app.state` consistently
  - safe (fail-open) with explicit logging when failing open
- Ensure scope rules are clean:
  - "apply only to public routes"
  - explicit exclude list (health endpoints)

**Deliverables:**

- cleaner wiring in app factory
- smaller middleware stack with intentional ordering
- tests that prove:
  - ordering is correct
  - exclusions work
  - headers appear only when enabled

### 3.4 "Heavy testing" plan (the core of Phase 02)

#### 3.4.1 Unit tests

**Focus:**

- auth service behavior (active/inactive, password verify)
- repository methods (constraints, queries)
- JWT behavior (claims, expiry, issuer/audience if used)
- error mapping utilities (status → code mapping)

**Outcome:**

- fast feedback, high coverage of logic

#### 3.4.2 Integration tests (real DB + Redis)

**Focus:**

- migrations run cleanly
- readiness endpoint reflects DB/Redis state correctly
- auth flow works end-to-end
- rate limit and cache toggles behave correctly when enabled (with Redis)
- standardized errors always include request id

**Outcome:**

- confidence the whole stack works together

#### 3.4.3 Black-box scenario tests (Python scripts)

Use/extend the existing scripts into a consistent "scenario runner" style:

- accepts base URL
- prints clear PASS/FAIL
- exits non-zero on failure
- can run locally and in CI
- can run repeated-load checks:
  - "hit endpoint 200 times"
  - validate rate limit triggers
  - validate headers remain consistent
  - validate no schema drift in responses
  - validate request id uniqueness rules (if applicable)

**Outcome:**

- "real world" API exercise beyond pytest

#### 3.4.4 Docker Compose smoke tests

Add a repeatable flow:

- `make up`
- run migrations
- run scenario scripts against the live stack
- optionally verify Redis keys for cache/rate limit
- optionally export and validate logs with the docker log exporter script

**Outcome:**

- confidence the template works as a productized stack, not just unit tests

#### 3.4.5 Performance-ish checks (optional, still lightweight)

Not full load testing, but sanity checks:

- repeated calls shouldn't leak memory or slow down drastically
- rate limiter uses atomic ops (already)
- request logging doesn't explode log volume unexpectedly (ensure single line per request remains true)

**Outcome:**

- template doesn't regress under basic repeated usage

## 4) Tooling + developer experience improvements (Phase 02)

### 4.1 Makefile becomes the "single interface"

Add or refine targets such as:

- `make smoke` (compose up + migrate + scenario verify + down)
- `make verify` (runs black-box verifiers against a running base URL)
- `make logs-export` (runs docker log export script for last N lines)
- keep `make test-unit`, `make test-integration`

### 4.2 CI becomes closer to production

Ensure CI runs:

- unit + integration tests
- at least one black-box verifier step (against a locally started server OR using TestClient mode if designed that way)
- optional compose smoke job (can be separate workflow, or nightly)

## 5) Documentation updates required in Phase 02

Because Phase 02 changes structure and possibly removes legacy behavior, docs must be updated as part of the change:

- `backend/docs/ARCHITECTURE.md` updated to match new module map
- `backend/docs/ONBOARDING.md` updated commands and file paths
- `backend/docs/ERROR_MODEL.md` confirmed as the only source of truth
- `backend/docs/RATE_LIMITING.md` confirmed with exact scope/exclusions
- folder READMEs updated to match new structure

Docs should remain:

- short, high-signal
- path-explicit (LLM-friendly)
- invariant-focused ("don't break these")

## 6) Expected Phase 02 acceptance criteria (definition of done)

Phase 02 is complete when all are true:

### Structure is clean and minimal

- redundant/legacy routers removed (or moved behind an explicit deprecation decision)
- no duplicated endpoints performing the same function in different places
- module boundaries are clear and enforceable

### All tests pass with high confidence

- unit + integration tests pass locally and in CI
- scenario scripts pass against live stack
- compose smoke flow passes (bring up → migrate → verify → (optional logs check))

### Scripts are reliable

- verification scripts have stable CLI usage and exit codes
- docker log export script is documented and proven in smoke checks

### Docs reflect reality

- paths and examples match code
- no contradictions between docs and implementation

