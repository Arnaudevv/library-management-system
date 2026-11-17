from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from ..models.loan import Loan
from .base_repository import BaseRepository


class LoanRepository(BaseRepository[Loan]):
    """Persist and query loans."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Loan)

    def get_by_id(self, loan_id: int) -> Optional[Loan]:
        statement = (
            select(Loan)
            .options(joinedload(Loan.book), joinedload(Loan.borrower))
            .where(Loan.id == loan_id)
        )
        return self.session.scalar(statement)

    def get_all(self) -> list[Loan]:
        statement = select(Loan).options(joinedload(Loan.book), joinedload(Loan.borrower))
        return list(self.session.scalars(statement).all())

    def get_by_book(self, book_id: int) -> list[Loan]:
        statement = (
            select(Loan)
            .options(joinedload(Loan.book), joinedload(Loan.borrower))
            .where(Loan.book_id == book_id)
        )
        return list(self.session.scalars(statement).all())

    def get_by_borrower(self, borrower_id: int) -> list[Loan]:
        statement = (
            select(Loan)
            .options(joinedload(Loan.book), joinedload(Loan.borrower))
            .where(Loan.borrower_id == borrower_id)
        )
        return list(self.session.scalars(statement).all())

    def get_active(self) -> list[Loan]:
        statement = (
            select(Loan)
            .options(joinedload(Loan.book), joinedload(Loan.borrower))
            .where(Loan.return_date.is_(None))
        )
        return list(self.session.scalars(statement).all())

    def get_history(self) -> list[Loan]:
        statement = (
            select(Loan)
            .options(joinedload(Loan.book), joinedload(Loan.borrower))
            .where(Loan.return_date.is_not(None))
        )
        return list(self.session.scalars(statement).all())

    def get_all_with_relations(self) -> list[Loan]:
        statement = select(Loan).options(joinedload(Loan.book), joinedload(Loan.borrower))
        return list(self.session.scalars(statement).all())

    def get_with_relations(self, loan_id: int) -> Optional[Loan]:
        statement = (
            select(Loan)
            .options(selectinload(Loan.book), selectinload(Loan.borrower))
            .where(Loan.id == loan_id)
        )
        return self.session.scalar(statement)
