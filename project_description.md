# FastAPI Template - Production-Ready Backend Foundation

## 1. Project Overview

### Goal

Build a reusable, production-grade FastAPI template that can be cloned and used as the base for multiple backend/API products.

### 🔥 Key Requirements

This base must be:

- **Production ready**
- **Maintainable**
- **Extensible**
- **Easy for humans to understand**
- **Easy for LLMs to reason about**

That last point is critical:

> Every important folder / feature / concern MUST have a Markdown explainer file so an LLM (or new teammate) can read, understand architecture, and generate code reliably.

---

## 2. Tech Stack

### Framework

- **Python 3.11+**
- **FastAPI**
- **Uvicorn**

### Database

- **PostgreSQL**
- **SQLAlchemy**
- **Alembic**

### Security

- **JWT auth** (OAuth2 password flow)
- **Passlib/Bcrypt**

### Infra

- **Redis** (rate limiting + caching)
- **Docker** / **docker-compose**

### Dev Experience

- **pytest**
- **black** / **isort** / **ruff**
- **pre-commit**
- **GitHub Actions** (or similar CI)

---

## 3. Repository Structure

👉 Plus required documentation files marking what each thing does

```
fastapi-template/
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── security.py
│   │   ├── rate_limit.py
│   │   ├── exceptions.py
│   │   ├── dependencies.py
│   │   └── README.md        <-- Explains core layer
│   │
│   ├── db/
│   │   ├── base.py
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── migrations/
│   │   └── README.md        <-- Explains DB layer
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── routes/
│   │   │   ├── router.py
│   │   │   └── README.md    <-- Explains API versioning and routing
│   │   └── deps.py
│   │
│   ├── schemas/
│   │   └── README.md        <-- Explains schema approach
│   │
│   ├── services/
│   │   └── README.md        <-- Explains service layer
│   │
│   ├── tasks/
│   │   └── README.md        <-- Explains background tasks
│   │
│   ├── telemetry/
│   │   └── README.md        <-- Explains observability strategy
│   │
│   ├── main.py
│   └── README.md            <-- Explains app lifecycle & startup
│
├── tests/
│   └── README.md            <-- Testing strategy doc
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ERROR_MODEL.md
│   ├── AUTH_MODEL.md
│   ├── RATE_LIMITING.md
│   └── ONBOARDING.md
│
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── .pre-commit-config.yaml
├── Makefile
└── README.md  <-- Primary entrypoint doc
```

---

## 4. LLM-Friendly Documentation Requirements

### Mandatory Documentation Rules

Every major module must have:

- **README.md**
  - Written in clear, structured English
  - Avoids ambiguity
  - Explains:
    - Purpose
    - Inputs / Outputs
    - How to extend
    - Example usage/comments
  - Broken into digestible logical sections so LLMs can parse easily

### Dedicated `/docs` Folder Must Include

| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | High-level architecture description |
| `AUTH_MODEL.md` | Full auth flow, JWT, dependencies |
| `ERROR_MODEL.md` | Standard error contract, examples |
| `RATE_LIMITING.md` | Strategy, Redis use, extension notes |
| `ONBOARDING.md` | How a new dev understands the project |

### Documentation Structure

Each document should have consistent headings:

- **Purpose** - What this module/feature does
- **Design** - Architectural decisions and rationale
- **How it works** - Step-by-step explanation
- **Extensibility Notes** - How to extend or customize
- **Examples** - Code examples and usage patterns

---

## Getting Started

This template provides a solid foundation for building production-ready FastAPI applications. Each module is documented to ensure clarity for both human developers and AI assistants.

### Quick Start

1. Clone this repository
2. Copy `.env.example` to `.env` and configure your environment variables
3. Run `docker-compose up` to start PostgreSQL and Redis
4. Run migrations: `alembic upgrade head`
5. Start the application: `uvicorn app.main:app --reload`

### Next Steps

- Read `/docs/ONBOARDING.md` for detailed setup instructions
- Review `/docs/ARCHITECTURE.md` to understand the system design
- Check individual module `README.md` files for specific implementation details

---

## Contributing

When adding new features:

1. Follow the modular structure
2. Add appropriate `README.md` files to new modules
3. Update relevant documentation in `/docs`
4. Ensure code follows the project's style guidelines (black, isort, ruff)
5. Add tests for new functionality

---

## License

[Specify your license here]

