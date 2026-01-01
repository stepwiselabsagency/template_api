.PHONY: up down logs fmt lint test precommit

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

precommit:
	@if [ "$$OS" = "Windows_NT" ] || uname -s | grep -qE "MINGW|MSYS|CYGWIN"; then \
		MSYS_NO_PATHCONV=1 cmd.exe /c ".venv\\Scripts\\python.exe -m pre_commit run --all-files"; \
	else \
		python -m pre_commit run --all-files; \
	fi
