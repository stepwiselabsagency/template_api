"""
ORM models.

Important: keep this module importing all models so Alembic autogenerate can
discover them via `Base.metadata`.
"""

from app.models.user import User

__all__ = ["User"]
