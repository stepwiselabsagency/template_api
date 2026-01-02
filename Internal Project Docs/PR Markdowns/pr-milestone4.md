# PR Title
`feat: Secure identity foundation (password hashing + JWT + login + auth deps)`

## Description
This PR implements the next milestone: **Secure Identity Foundation**. It adds a reusable, security-minded authentication baseline to the FastAPI template: **bcrypt password hashing**, **JWT (HS256) issuance/verification**, a standard **OAuth2 password login** endpoint, and reusable dependencies for **current user** and **minimal RBAC** — while keeping `/health` unchanged and preserving Docker/compose workflows.

## Changes
- **Auth module (`backend/app/auth/`)**:
  - Added `password.py`:
    - `hash_password(plain: str) -> str` (bcrypt via `passlib`)
    - `verify_password(plain: str, hashed: str) -> bool`
  - Added `jwt.py`:
    - `create_access_token(subject, expires_delta=None, additional_claims=None) -> str`
    - `decode_token(token) -> dict` (validates signature + exp; optional issuer/audience)
    - Enforces `sub` presence/shape and uses conservative clock skew leeway.
  - Added `service.py`:
    - `authenticate_user(db, email, password) -> User | None`
    - `issue_token_for_user(user) -> dict` returning `{access_token, token_type, expires_in}`
  - Added `dependencies.py`:
    - `get_current_user(...) -> User` (401 with `WWW-Authenticate: Bearer` on failure)
    - `require_roles(*roles)` dependency helper
    - Minimal template RBAC role mapping via `is_superuser -> "admin"` (also emits `roles` claim)
- **Auth API routes (`backend/app/api/routes/auth.py`)**:
  - Added `POST /auth/login` using `OAuth2PasswordRequestForm`
    - `Content-Type: application/x-www-form-urlencoded`
    - `username` is treated as **email** in this template
    - Invalid creds and inactive users both return `401` (no user status leakage)
  - Added `GET /auth/me` protected route returning current user basics
- **Router wiring**:
  - Updated `backend/app/api/router.py` to include the auth router.
- **Settings (`backend/app/core/config.py`)**:
  - Added JWT settings:
    - `JWT_SECRET_KEY` (required outside `local/test`)
    - `JWT_ALGORITHM` (default `HS256`)
    - `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` (default `60`)
    - Optional: `JWT_ISSUER`, `JWT_AUDIENCE`
  - Redacts `JWT_SECRET_KEY` in `model_dump_safe()`.
- **Security wrapper (`backend/app/core/security.py`)**:
  - Removed the old SHA-256 placeholder hashing.
  - Kept the module as a backwards-compatible wrapper exporting `hash_password`/`verify_password` from `app/auth/password.py`.
- **User model + migration**:
  - Updated `backend/app/models/user.py` to add `is_superuser: bool = False`.
  - Added Alembic migration `backend/alembic/versions/0002_add_is_superuser_to_users.py`.
- **Repository enhancement**:
  - Updated `UserRepository.create(...)` to accept `is_superuser: bool = False`.
- **Dependencies**:
  - Pinned minimal auth deps in `pyproject.toml`:
    - `passlib[bcrypt]==1.7.4`
    - `PyJWT==2.10.1`
- **.env example**:
  - Updated `.env.example` to include JWT settings + common compose defaults.
- **Tests**:
  - Added `backend/tests/test_auth.py`:
    - Login success returns token
    - Wrong password returns 401 + `WWW-Authenticate: Bearer`
    - Token can access `/auth/me`
    - Uses dependency overrides + SQLite for deterministic, Docker-free tests
- **Docs**:
  - Added `backend/docs/AUTH_MODEL.md` describing:
    - password hashing approach
    - JWT claim model
    - login flow + curl examples
    - protecting routes + role dependency
    - security checklist + extension points

## Milestone Completion Criteria
- [x] Login works end-to-end (`/auth/login` returns a JWT on valid credentials).
- [x] JWT creation/verification implemented with safe defaults and validation.
- [x] Password hashing implemented using a modern, supported library (bcrypt via passlib).
- [x] `get_current_user()` dependency implemented + protected route example (`/auth/me`).
- [x] Minimal RBAC foundation implemented (`is_superuser` + `require_roles`).
- [x] Auth model documented (`backend/docs/AUTH_MODEL.md`).
- [x] Tooling passes: `make fmt`, `make lint`, `make test`, `make precommit`.
- [x] `/health` remains unchanged (`/health` → `{"status":"ok"}`).

## Notes / Design Decisions
- **OAuth2PasswordRequestForm**: chosen for FastAPI-standard login flow. We treat `username` as an email to avoid introducing non-standard field names.
- **JWT strategy**:
  - Minimal claims: `sub`, `iat`, `exp` (+ optional `roles`, `iss`, `aud`).
  - Optional issuer/audience validation is available via settings.
  - Conservative leeway for clock skew (30s).
- **Role model**:
  - Minimal template-friendly RBAC: `is_superuser` boolean.
  - `require_roles("admin")` maps to `is_superuser`.
  - Docs explain how to expand to a multi-role RBAC system later.
- **No secret leakage**:
  - Settings redact `JWT_SECRET_KEY` in safe dumps.
  - Passwords are never logged or returned.

## Related
- Milestone: Secure Identity Foundation (Auth baseline)
- Closes #4 (if applicable)

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
curl -i http://localhost:8000/health
# expect: HTTP 200, body {"status":"ok"}, and header X-Request-ID present

# 3. Run migrations
make db-upgrade

# 4. Create a user (existing route; hashes password with bcrypt now)
curl -i -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test123456@example.com","password":"pass123"}'
# expect: HTTP 201

# 5. Login (OAuth2 form)
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test123456@example.com&password=pass123"
# expect: HTTP 200 with JSON access_token + token_type=bearer

# 6. Use token on protected route
# Replace <token> with the returned access_token
curl -i http://localhost:8000/auth/me \
  -H "Authorization: Bearer <token>"
# expect: HTTP 200 with {id, email, is_active, is_superuser}

# 7. Verify tooling
make fmt
make lint
make test
make precommit
```


