from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all ORM models.

    Alembic uses `Base.metadata` as the migration target metadata.
    """
