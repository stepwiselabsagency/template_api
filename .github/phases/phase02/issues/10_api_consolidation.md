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
