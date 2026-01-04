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
