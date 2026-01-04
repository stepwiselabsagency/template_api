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

