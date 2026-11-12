from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models.author import Author
from .base_repository import BaseRepository


class AuthorRepository(BaseRepository[Author]):
    """Persist and query authors."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Author)

    def get_by_name(self, name: str) -> Optional[Author]:
        return self.session.scalar(select(Author).where(Author.name == name))

    def search_by_name(self, text: str) -> list[Author]:
        return list(self.session.scalars(select(Author).where(Author.name.ilike(f"%{text}%"))).all())

    def get_with_books(self, author_id: int) -> Optional[Author]:
        statement = select(Author).options(selectinload(Author.books)).where(Author.id == author_id)
        return self.session.scalar(statement)
