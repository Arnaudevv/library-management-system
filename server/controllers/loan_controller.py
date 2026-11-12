from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from ..dto import LoanDTO
from ..persistance.models.loan import Loan
from ..service.loan_service import LoanService


class LoanController:
    """Validate loan input and convert service results to response DTOs."""

    def __init__(self, service: LoanService) -> None:
        self.service = service

    def create(self, body: dict[str, Any]) -> LoanDTO:
        return self._to_dto(self.service.save(self._from_body(body)))

    def get_by_id(self, loan_id: int) -> Optional[LoanDTO]:
        self._validate_id(loan_id)
        return self._to_dto(self.service.get_by_id(loan_id))

    def get_all(self) -> list[LoanDTO]:
        return [self._to_dto(loan) for loan in self.service.get_all()]

    def get_by_book(self, book_id: int) -> list[LoanDTO]:
        self._validate_id(book_id)
        return [self._to_dto(loan) for loan in self.service.get_by_book(book_id)]

    def get_by_borrower(self, borrower_id: int) -> list[LoanDTO]:
        self._validate_id(borrower_id)
        return [self._to_dto(loan) for loan in self.service.get_by_borrower(borrower_id)]

    def get_active(self) -> list[LoanDTO]:
        return [self._to_dto(loan) for loan in self.service.get_active()]

    def get_history(self) -> list[LoanDTO]:
        return [self._to_dto(loan) for loan in self.service.get_history()]

    def get_all_with_relations(self) -> list[LoanDTO]:
        return [self._to_dto(loan) for loan in self.service.get_all_with_relations()]

    def get_with_relations(self, loan_id: int) -> Optional[LoanDTO]:
        self._validate_id(loan_id)
        return self._to_dto(self.service.get_with_relations(loan_id))

    def delete(self, loan_id: int) -> bool:
        self._validate_id(loan_id)
        return self.service.delete(loan_id)

    def count(self) -> int:
        return self.service.count()

    @classmethod
    def _from_body(cls, body: dict[str, Any]) -> LoanDTO:
        if not isinstance(body, dict):
            raise ValueError("Request body must be a JSON object")
        book_id = body.get("book_id")
        borrower_id = body.get("borrower_id")
        loan_date = cls._parse_date(body.get("loan_date"), "loan_date")
        return_date = cls._parse_date(body.get("return_date"), "return_date")
        cls._validate_id(book_id, "book_id")
        cls._validate_id(borrower_id, "borrower_id")
        return LoanDTO(
            book_id=book_id,
            borrower_id=borrower_id,
            loan_date=loan_date,
            return_date=return_date,
        )

    @staticmethod
    def _to_dto(loan: Optional[Loan]) -> Optional[LoanDTO]:
        if loan is None:
            return None
        return LoanDTO(
            id=loan.id,
            book_id=loan.book_id,
            borrower_id=loan.borrower_id,
            loan_date=loan.loan_date,
            return_date=loan.return_date,
        )

    @staticmethod
    def _parse_date(value: Any, field: str) -> Optional[dt.date]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{field} must be an ISO date")
        try:
            return dt.date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(f"{field} must be an ISO date") from error

    @staticmethod
    def _validate_id(value: Any, field: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{field} must be a positive integer")
