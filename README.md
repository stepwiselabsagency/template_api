# template-api

Minimal FastAPI backend template with:

- **Versioned API baseline** under `/api/v1`
- **Standard error envelope** + request id correlation
- Optional **rate limiting**, **cache**, and **telemetry hooks**
- Docker Compose + Make targets for repeatable dev/CI workflows

## Start here (30-minute onboarding path)

- **Read**: `backend/docs/ONBOARDING.md`
- **Run** (Docker quickstart below) and verify `GET /health`
- **Skim**:
  - `backend/docs/ARCHITECTURE.md` (request flow + extension points)
  - `backend/docs/ERROR_MODEL.md` (client contract)
  - `backend/docs/RATE_LIMITING.md` (scope/headers/fail-open)
  - `backend/docs/AUTH_MODEL.md`

## Prerequisites

- Docker + Docker Compose (`docker compose` or `docker-compose`)
- Python 3.10+ (for local dev tooling + pre-commit)
- Git (required by pre-commit)
- Windows: use **Git Bash** (or WSL) for `make` targets

## 5-minute quick start (fresh clone)

```bash
cp env.example .env
make up
curl http://localhost:8000/health
```

Expected (must remain stable):

```json
{"status":"ok"}
```

## Ports

| Service | Host | Container |
|---|---:|---:|
| app | 8000 | 8000 |
| postgres | 5432 | 5432 |
| redis | 6379 | 6379 |

## Docs index (LLM-friendly)

- Onboarding: `backend/docs/ONBOARDING.md`
- Architecture: `backend/docs/ARCHITECTURE.md`
- Error model (client contract): `backend/docs/ERROR_MODEL.md`
- Rate limiting: `backend/docs/RATE_LIMITING.md`
- Auth model: `backend/docs/AUTH_MODEL.md`
- Hardening overview: `backend/docs/PROD_HARDENING.md`

## Project structure (high signal)

```text
repo-root/
|-- backend/                  # FastAPI app package + migrations + tests
|   |-- app/                  # application code (core, api, auth, db, models, repos)
|   |-- alembic/              # schema migrations
|   |-- tests/                # unit + integration tests
|   |-- docs/                 # template docs (onboarding/architecture/error model/...)
|-- scripts/                  # repo utilities (non-runtime)
|-- docker-compose.yml        # local infra (app + postgres + redis)
|-- Dockerfile                # container build
|-- Makefile                  # repeatable dev commands (fmt/lint/test/db-*)
|-- env.example               # example env vars
`-- pyproject.toml            # deps + tooling
```

## Developer tooling (repeatable)

Create and activate a venv, then install dev deps:

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows (Git Bash)
source .venv/Scripts/activate

pip install -e ".[dev]"
```

Run formatting / lint / tests:

```bash
make fmt
make lint
make test
```

Pre-commit:

```bash
pre-commit install
make precommit
```

## Stop the stack

```bash
make down
```

## Troubleshooting

- **Ports already in use**: stop the conflicting process or change host ports in `.env` / `docker-compose.yml`.
- **Docker not running**: start Docker Desktop / daemon and retry `make up`.
- **Pre-commit git error**: if `make precommit` fails with `Executable 'git' not found`, ensure your venv is active and try running `python -m pre_commit run --all-files` directly.
