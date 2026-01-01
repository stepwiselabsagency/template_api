# PR Title
`feat: Initialize repository with dev tooling and Docker Compose`

## Description
This PR implements the first milestone: **Repo + Dev Tooling + Docker Compose**. It establishes a clean Python backend structure, containerized local infrastructure, and automated developer workflows (formatting, linting, and pre-commit hooks).

## Changes
- **Backend Skeleton**: Initialized FastAPI application in `backend/` with a `/health` endpoint and startup lifespan logic.
- **Docker Infrastructure**: Created root `docker-compose.yml` and `Dockerfile` running the app, PostgreSQL 16, and Redis 7.
- **Developer Tooling**: 
    - Added `Makefile` with targets for `up`, `down`, `fmt`, `lint`, `test`, and `precommit`.
    - Configured `pyproject.toml` with pinned dependencies for `black`, `isort`, `ruff`, and `pytest`.
    - Added `.pre-commit-config.yaml` with automated hooks.
- **Environment**: Created `.env.example` with standard local development defaults.
- **Documentation**: Overwrote root `README.md` with clear quick-start instructions, ports table, and troubleshooting tips for Windows/Git Bash.

## Milestone Completion Criteria
- [x] `make up` starts the stack cleanly.
- [x] `curl http://localhost:8000/health` returns `{"status":"ok"}`.
- [x] `make fmt` and `make lint` run without conflicts.
- [x] `make precommit` passes all hooks (including Git Bash fixes).

## Related
- Milestone: Repo + Dev Tooling + Docker Compose
- Closes #1 (if applicable)

---

## Validation Commands for Reviewer
```bash
# 1. Setup environment
cp .env.example .env
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -e ".[dev]"

# 2. Run stack
make up
curl http://localhost:8000/health

# 3. Verify tooling
make fmt
make lint
make test
make precommit
```

