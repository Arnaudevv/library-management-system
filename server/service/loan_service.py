from __future__ import annotations

import datetime as dt
from typing import Optional

from ..dto import LoanDTO
from ..persistance.models.loan import Loan
from ..persistance.repositories.book_repository import BookRepository
from ..persistance.repositories.borrower_repository import BorrowerRepository
from ..persistance.repositories.loan_repository import LoanRepository
from ..persistance.repositories.unit_of_work import UnitOfWorkFactory


class LoanService:
    """Apply loan business rules and coordinate loan repositories."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def get_by_id(self, loan_id: int) -> Optional[Loan]:
        with self.uow_factory.create() as uow:
            return LoanRepository(uow.session).get_by_id(loan_id)

    def get_all(self) -> list[Loan]:
        with self.uow_factory.create() as uow:
            return LoanRepository(uow.session).get_all()

    def get_by_book(self, book_id: int) -> list[Loan]:
        with self.uow_factory.create() as uow:
            return LoanRepository(uow.session).get_by_book(book_id)

    def get_by_borrower(self, borrower_id: int) -> list[Loan]:
        with self.uow_factory.create() as uow:
            return LoanRepository(uow.session).get_by_borrower(borrower_id)

    def get_active(self) -> list[Loan]:
        with self.uow_factory.create() as uow:
            return LoanRepository(uow.session).get_active()

    def get_history(self) -> list[Loan]:
        with self.uow_factory.create() as uow:
            return LoanRepository(uow.session).get_history()

    def get_all_with_relations(self) -> list[Loan]:
        with self.uow_factory.create() as uow:
            return LoanRepository(uow.session).get_all_with_relations()

    def get_with_relations(self, loan_id: int) -> Optional[Loan]:
        with self.uow_factory.create() as uow:
            return LoanRepository(uow.session).get_with_relations(loan_id)

    def save(self, loan: LoanDTO) -> Loan:
        with self.uow_factory.create() as uow:
            book_repository = BookRepository(uow.session)
            borrower_repository = BorrowerRepository(uow.session)
            if book_repository.get_by_id(loan.book_id) is None:
                raise ValueError("The book does not exist")
            if borrower_repository.get_by_id(loan.borrower_id) is None:
                raise ValueError("The borrower does not exist")
            loan_repository = LoanRepository(uow.session)
            if any(
                existing.return_date is None
                for existing in loan_repository.get_by_book(loan.book_id)
            ):
                raise ValueError("The book already has an active loan")
            entity = Loan(
                book_id=loan.book_id,
                borrower_id=loan.borrower_id,
                return_date=loan.return_date,
            )
            if loan.loan_date is not None:
                entity.loan_date = loan.loan_date
            saved = loan_repository.save(entity)
            uow.session.flush()
            return saved

    def delete(self, loan_id: int) -> bool:
        with self.uow_factory.create() as uow:
            repository = LoanRepository(uow.session)
            loan = repository.get_by_id(loan_id)
            if loan is None:
                return False
            repository.delete(loan)
            return True

    def count(self) -> int:
        with self.uow_factory.create() as uow:
            return LoanRepository(uow.session).count()
