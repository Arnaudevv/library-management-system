from __future__ import annotations

from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session


T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Provide common persistence operations for one model."""

    def __init__(self, session: Session, model: Type[T]) -> None:
        self.session = session
        self.model = model

    def get_by_id(self, entity_id: int) -> Optional[T]:
        return self.session.get(self.model, entity_id)

    def get_all(self) -> list[T]:
        return list(self.session.scalars(select(self.model)).all())

    def save(self, entity: T) -> T:
        self.session.add(entity)
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)

    def count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(self.model)) or 0
