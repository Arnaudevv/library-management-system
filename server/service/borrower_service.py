from __future__ import annotations

from typing import Optional

from ..dto import BorrowerDTO
from ..persistance.models.borrower import Borrower
from ..persistance.repositories.borrower_repository import BorrowerRepository
from ..persistance.repositories.unit_of_work import UnitOfWorkFactory


class BorrowerService:
    """Apply borrower business rules and coordinate borrower repositories."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def get_by_id(self, borrower_id: int) -> Optional[Borrower]:
        with self.uow_factory.create() as uow:
            return BorrowerRepository(uow.session).get_by_id(borrower_id)

    def get_all(self) -> list[Borrower]:
        with self.uow_factory.create() as uow:
            return BorrowerRepository(uow.session).get_all()

    def get_by_email(self, email: str) -> Optional[Borrower]:
        with self.uow_factory.create() as uow:
            return BorrowerRepository(uow.session).get_by_email(email)

    def search_by_name(self, text: str) -> list[Borrower]:
        with self.uow_factory.create() as uow:
            return BorrowerRepository(uow.session).search_by_name(text)

    def get_with_loans(self, borrower_id: int) -> Optional[Borrower]:
        with self.uow_factory.create() as uow:
            return BorrowerRepository(uow.session).get_with_loans(borrower_id)

    def save(self, borrower: BorrowerDTO) -> Borrower:
        with self.uow_factory.create() as uow:
            repository = BorrowerRepository(uow.session)
            if repository.get_by_email(borrower.email) is not None:
                raise ValueError("A borrower with this email already exists")
            entity = Borrower(name=borrower.name, email=borrower.email)
            saved = repository.save(entity)
            uow.session.flush()
            return saved

    def delete(self, borrower_id: int) -> bool:
        with self.uow_factory.create() as uow:
            repository = BorrowerRepository(uow.session)
            borrower = repository.get_by_id(borrower_id)
            if borrower is None:
                return False
            repository.delete(borrower)
            return True

    def count(self) -> int:
        with self.uow_factory.create() as uow:
            return BorrowerRepository(uow.session).count()
