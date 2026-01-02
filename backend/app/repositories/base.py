from __future__ import annotations

from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, instance) -> None:
        self.db.add(instance)

    def delete(self, instance) -> None:
        self.db.delete(instance)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance) -> None:
        self.db.refresh(instance)
