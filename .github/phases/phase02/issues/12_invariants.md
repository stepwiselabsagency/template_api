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
