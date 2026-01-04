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
