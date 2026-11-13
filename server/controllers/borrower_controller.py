from __future__ import annotations

from typing import Any, Optional

from ..dto import BorrowerDTO
from ..persistance.models.borrower import Borrower
from ..protocol.errors import ResourceNotFoundError, ValidationError
from ..services.borrower_service import BorrowerService


class BorrowerController:
    """Validate borrower input and convert service results to response DTOs."""

    def __init__(self, service: BorrowerService) -> None:
        self.service = service

    def create(self, body: dict[str, Any]) -> BorrowerDTO:
        return self._to_dto(self.service.save(self._from_body(body)))

    def get_by_id(self, borrower_id: int) -> Optional[BorrowerDTO]:
        self._validate_id(borrower_id)
        borrower = self.service.get_by_id(borrower_id)
        if borrower is None:
            raise ResourceNotFoundError(code="borrower_not_found", message="The borrower does not exist.")
        return self._to_dto(borrower)

    def get_all(self) -> list[BorrowerDTO]:
        return [self._to_dto(borrower) for borrower in self.service.get_all()]

    def get_by_email(self, email: str) -> Optional[BorrowerDTO]:
        self._validate_text(email, "email")
        borrower = self.service.get_by_email(email)
        if borrower is None:
            raise ResourceNotFoundError(code="borrower_not_found", message="The borrower does not exist.")
        return self._to_dto(borrower)

    def search_by_name(self, text: str) -> list[BorrowerDTO]:
        self._validate_text(text, "text")
        return [self._to_dto(borrower) for borrower in self.service.search_by_name(text)]

    def get_with_loans(self, borrower_id: int) -> Optional[BorrowerDTO]:
        self._validate_id(borrower_id)
        return self._to_dto(self.service.get_with_loans(borrower_id))

    def delete(self, borrower_id: int) -> bool:
        self._validate_id(borrower_id)
        if not self.service.delete(borrower_id):
            raise ResourceNotFoundError(code="borrower_not_found", message="The borrower does not exist.")
        return True

    def count(self) -> int:
        return self.service.count()

    @classmethod
    def _from_body(cls, body: dict[str, Any]) -> BorrowerDTO:
        if not isinstance(body, dict):
            if body is None:
                raise ValidationError(code="missing_request_body", message="Request body is required.")
            raise ValidationError(code="invalid_request_body", message="Request body must be a JSON object.")
        name = body.get("name")
        email = body.get("email")
        cls._validate_text(name, "name")
        cls._validate_text(email, "email")
        if "@" not in email:
            raise ValidationError(code="invalid_email", message="email must be a valid email address.")
        return BorrowerDTO(name=name, email=email)

    @staticmethod
    def _to_dto(borrower: Optional[Borrower]) -> Optional[BorrowerDTO]:
        if borrower is None:
            return None
        return BorrowerDTO(id=borrower.id, name=borrower.name, email=borrower.email)

    @staticmethod
    def _validate_id(value: Any) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValidationError(code="invalid_id", message="ID must be a positive integer.")

    @staticmethod
    def _validate_text(value: Any, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(code="invalid_field_value", message=f"{field} must be a non-empty string.")
