from __future__ import annotations

from typing import Optional

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, joinedload, selectinload

from ..models.book import Book
from ..models.loan import Loan
from .base_repository import BaseRepository


class BookRepository(BaseRepository[Book]):
    """Persist and query books."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Book)

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        return self.session.scalar(select(Book).where(Book.isbn == isbn))

    def search_by_title(self, text: str) -> list[Book]:
        return list(self.session.scalars(select(Book).where(Book.title.ilike(f"%{text}%"))).all())

    def get_by_author(self, author_id: int) -> list[Book]:
        return list(self.session.scalars(select(Book).where(Book.author_id == author_id)).all())

    def get_all_with_authors(self) -> list[Book]:
        statement = select(Book).options(joinedload(Book.author))
        return list(self.session.scalars(statement).all())

    def get_with_loans(self, book_id: int) -> Optional[Book]:
        statement = select(Book).options(selectinload(Book.loans)).where(Book.id == book_id)
        return self.session.scalar(statement)

    def get_available(self) -> list[Book]:
        active_loan = exists().where(Loan.book_id == Book.id, Loan.return_date.is_(None))
        return list(self.session.scalars(select(Book).where(~active_loan)).all())
