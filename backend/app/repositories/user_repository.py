from __future__ import annotations

import uuid

from app.models.user import User
from app.repositories.base import BaseRepository
from sqlalchemy import Select, select, update


class UserRepository(BaseRepository):
    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt: Select[tuple[User]] = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> User | None:
        stmt: Select[tuple[User]] = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def create(
        self,
        *,
        email: str,
        hashed_password: str,
        is_active: bool = True,
        is_superuser: bool = False,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            is_active=is_active,
            is_superuser=is_superuser,
        )
        self.add(user)
        self.commit()
        self.refresh(user)
        return user

    def list(self, *, limit: int = 50, offset: int = 0) -> list[User]:
        stmt: Select[tuple[User]] = (
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        return list(self.db.scalars(stmt).all())

    def set_active(self, user_id: uuid.UUID, is_active: bool) -> User | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_active=is_active)
            .returning(User)
        )
        updated = self.db.execute(stmt).scalar_one_or_none()
        if updated is None:
            return None
        self.commit()
        return updated
