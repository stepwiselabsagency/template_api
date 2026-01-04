.PHONY: up down logs fmt lint test test-unit test-integration precommit
.PHONY: db-upgrade db-downgrade db-revision

# Prefer Docker Compose v2 (`docker compose`), fallback to legacy v1 (`docker-compose`).
DC ?= $(shell \
	if docker compose version >/dev/null 2>&1; then echo "docker compose"; \
	elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; \
	else echo "docker compose"; fi \
)

up:
	$(DC) up -d --build

down:
	$(DC) down

logs:
	$(DC) logs -f --tail=200

fmt:
	python -m isort backend
	python -m black backend

lint:
	python -m ruff check backend

test:
	python -m pytest -q

test-unit:
	python -m pytest -q backend/tests/unit

test-integration:
	python -m pytest -q backend/tests -m "not unit"

precommit:
	@if [ "$$OS" = "Windows_NT" ] || uname -s | grep -qE "MINGW|MSYS|CYGWIN"; then \
		MSYS_NO_PATHCONV=1 cmd.exe /c ".venv\\Scripts\\python.exe -m pre_commit run --all-files"; \
	else \
		python -m pre_commit run --all-files; \
	fi

# --- Database / Alembic helpers ---
db-upgrade:
	$(DC) exec -T app alembic -c backend/alembic.ini upgrade head

db-downgrade:
	$(DC) exec -T app alembic -c backend/alembic.ini downgrade -1

db-revision:
	$(DC) exec -T app alembic -c backend/alembic.ini revision --autogenerate -m "$(msg)"
