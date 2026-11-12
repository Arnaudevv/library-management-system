from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models.borrower import Borrower
from .base_repository import BaseRepository


class BorrowerRepository(BaseRepository[Borrower]):
    """Persist and query borrowers."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Borrower)

    def get_by_email(self, email: str) -> Optional[Borrower]:
        return self.session.scalar(select(Borrower).where(Borrower.email == email))

    def search_by_name(self, text: str) -> list[Borrower]:
        return list(self.session.scalars(select(Borrower).where(Borrower.name.ilike(f"%{text}%"))).all())

    def get_with_loans(self, borrower_id: int) -> Optional[Borrower]:
        statement = select(Borrower).options(selectinload(Borrower.loans)).where(Borrower.id == borrower_id)
        return self.session.scalar(statement)
