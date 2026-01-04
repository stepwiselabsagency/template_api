# `scripts/` — Repo utilities (non-runtime)

## Purpose

- Contains developer utilities and debugging helpers. These scripts are **not part of runtime** behavior of the API.

## Key modules/files

- **Prod-hardening verification**: `scripts/automated_tests/verify_prod_hardening.py`
- **Docker logs exporter**: `scripts/docker_logs/export_docker_logs_json.py`

## How it connects

- Scripts typically operate on Docker logs or validate template behaviors without modifying the app.

## Extension points

- Add a new script under a subfolder and keep it single-purpose.
- Prefer scripts that are runnable with `python <script>.py` and accept args/env vars explicitly.

## Pitfalls / invariants

- Do not make scripts required for runtime.
- Keep scripts cloud-neutral and avoid vendor-specific assumptions.

## Related docs

- `backend/docs/PROD_HARDENING.md`
- `backend/tests/README.md`


