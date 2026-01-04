# PR Title
`docs: elite onboarding + architecture/error/rate-limit docs + folder READMEs (no behavior change)`

## Description
This PR completes **Milestone 8: “Make this template elite”** by adding a high-signal, **LLM-friendly documentation suite** plus short folder READMEs across the backend. The docs are designed so a new developer can onboard in **< 30 minutes**, and so an LLM can reason cleanly about architecture and extension points.

Key non-negotiables preserved:

- Existing endpoints and successful response schemas remain unchanged.
- `GET /health` still returns exactly `{"status":"ok"}`.
- Existing routing/versioning behavior remains intact (`/api/v1` stays `/api/v1`).
- No new runtime dependencies (docs-only changes).

---

## Changes

### New docs suite (single location: `backend/docs/`)
Added a consistent “docs home” under `backend/docs/`:

- `backend/docs/ONBOARDING.md`
  - 30-minute onboarding path
  - prerequisites (includes Windows Git Bash note)
  - 5-minute quickstart commands
  - mental model (request flow, config, DB, auth)
  - common tasks (“where do I change X?”)
  - test commands + CI parity tips
  - “where to read next” links

- `backend/docs/ARCHITECTURE.md`
  - Mermaid diagram of request flow (client → middleware → routing → dependencies → repos → DB/Redis → response)
  - explicit subsystem sections with:
    - purpose
    - key file paths
    - extension points
    - invariants/do-not-break rules
  - app factory creation path: `backend/app/core/app_factory.py`
  - settings lifecycle + caching: `backend/app/core/config.py:get_settings`
  - middleware ordering and Starlette “reverse apply” behavior
  - routing/versioning strategy (`/api/v1` vs legacy routes)
  - dependency injection patterns (`get_db`, `get_current_user`, cache dep)
  - hardening layer overview (errors/handlers/rate limit/cache/telemetry)

- `backend/docs/ERROR_MODEL.md` (single source of truth)
  - standard error schema and meaning of each field (`code`, `message`, `request_id`, `details`)
  - mapping rules:
    - 422 validation
    - 401/403 auth
    - 404 not found
    - 409 conflict (both `HTTPException` and DB integrity handler)
    - 429 rate-limited
    - 500 internal
  - curl examples + example JSON bodies
  - identifies exact handlers that generate the schema (`backend/app/core/exception_handlers.py`)
  - documents header preservation (e.g., `WWW-Authenticate`)

- `backend/docs/RATE_LIMITING.md`
  - enablement env vars
  - scope rules (only `/api/v1/*`) + exclusions:
    - `/health`, `/api/v1/health/live`, `/api/v1/health/ready`
  - algorithm summary:
    - fixed-window + Redis Lua atomicity
  - keying strategy (truthful to implementation: `ip` vs `user_or_ip`)
  - headers semantics (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`)
  - fail-open behavior and rationale
  - local testing instructions (with/without Redis)
  - how to swap implementation via `RateLimiter` protocol

### Reconcile existing docs (reduce duplication)
Updated existing docs to cross-link and avoid contradictions:

- `backend/docs/PROD_HARDENING.md`
  - now serves as an overview/index pointing to source-of-truth docs
  - removed duplicated error/rate-limit writeups that can drift

- `backend/docs/AUTH_MODEL.md`
  - added cross-links to onboarding/architecture/error model

### Folder READMEs for major directories
Added short, structured `README.md` files so readers can navigate the repo quickly:

- `backend/README.md`
- `backend/app/README.md`
- `backend/app/api/README.md`
- `backend/app/auth/README.md`
- `backend/app/core/cache/README.md`
- `backend/app/core/rate_limit/README.md`
- `backend/app/models/README.md`
- `backend/app/repositories/README.md`
- `scripts/README.md`

Upgraded existing folder READMEs for accuracy and linking:

- `backend/app/api/v1/README.md`
  - fixed mismatch: conflict response is documented as the standard error envelope (not raw `{"detail": ...}`)

- `backend/app/core/README.md`
  - clarified Starlette middleware ordering (“reverse apply”)
  - aligned documented effective order with current wiring (request id, telemetry, request logging, rate limiting)

### Root `README.md` upgrade (“Start here”)
Updated root `README.md` to:

- include a 30-minute onboarding path pointing to `backend/docs/ONBOARDING.md`
- include a docs index for quick navigation
- keep the `/health` response documented exactly
- replace the noisy “tracked files” dump with a high-signal structure overview

---

## Milestone Completion Criteria
- [x] Added required docs: `ONBOARDING.md`, `ARCHITECTURE.md`, `ERROR_MODEL.md`, `RATE_LIMITING.md`
- [x] Ensured major folders have short READMEs with purpose + links
- [x] Reconciled/cross-linked existing docs to avoid duplication and drift
- [x] Updated root `README.md` with onboarding path + docs index
- [x] Validation commands pass (`make fmt`, `make lint`, `make test`, `make precommit`)

---

## Notes / Design Decisions
- **Docs live in one place**: chose `backend/docs/` to avoid splitting docs across repo root and backend.
- **LLM-friendly writing**: stable terminology (“v1 routes”, “legacy routes”, “hardening layer”), explicit file paths, and repeated “where to change X?” callouts.
- **No behavior changes**: this milestone is documentation-only; no public API behavior was modified.

---

## Validation Commands for Reviewer

```bash
make fmt
make lint
make test
make precommit
```


