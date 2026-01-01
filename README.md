# template-api

Minimal Python backend starter with Docker Compose + developer tooling (format/lint/test + pre-commit).

## Prerequisites

- Docker + Docker Compose (`docker compose` or `docker-compose`)
- Python 3.10+ (for local dev tooling + pre-commit)
- Git (required by pre-commit)

## Quick start (fresh clone)

```bash
cp .env.example .env
make up
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok"}
```

## Ports

| Service | Host | Container |
|---|---:|---:|
| app | 8000 | 8000 |
| postgres | 5432 | 5432 |
| redis | 6379 | 6379 |

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
