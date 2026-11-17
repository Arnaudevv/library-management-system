from __future__ import annotations

import datetime as dt
from typing import Optional

from ..dto import LoanDTO
from ..persistance.models.loan import Loan
from ..persistance.repositories.book_repository import BookRepository
from ..persistance.repositories.borrower_repository import BorrowerRepository
from ..persistance.repositories.loan_repository import LoanRepository
from ..persistance.repositories.unit_of_work import UnitOfWorkFactory
from ..protocol.errors import ConflictError, ResourceNotFoundError


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
            book = book_repository.get_by_id(loan.book_id)
            if book is None:
                raise ResourceNotFoundError(
                    code="book_not_found",
                    message="The book does not exist.",
                )
            borrower = borrower_repository.get_by_id(loan.borrower_id)
            if borrower is None:
                raise ResourceNotFoundError(
                    code="borrower_not_found",
                    message="The borrower does not exist.",
                )
            loan_repository = LoanRepository(uow.session)
            if any(
                existing.return_date is None
                for existing in loan_repository.get_by_book(loan.book_id)
            ):
                raise ConflictError(
                    code="book_already_loaned",
                    message="The book already has an active loan.",
                )
            entity = Loan(
                book=book,
                borrower=borrower,
                due_date=loan.due_date,
            )
            saved = loan_repository.save(entity)
            uow.session.flush()
            return saved

    def return_loan(self, loan_id: int) -> Loan:
        with self.uow_factory.create() as uow:
            repository = LoanRepository(uow.session)
            loan = repository.get_by_id(loan_id)
            if loan is None:
                raise ResourceNotFoundError(
                    code="loan_not_found",
                    message="The loan does not exist.",
                )
            if loan.return_date is not None:
                raise ConflictError(
                    code="loan_already_returned",
                    message="The loan has already been returned.",
                )
            loan.return_date = dt.date.today()
            uow.session.flush()
            return loan

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
