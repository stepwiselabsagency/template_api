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
