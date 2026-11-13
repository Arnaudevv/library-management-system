from __future__ import annotations

from typing import Any, Optional

from ..dto import AuthorDTO
from ..persistance.models.author import Author
from ..protocol.errors import ResourceNotFoundError, ValidationError
from ..services.author_service import AuthorService


class AuthorController:
    """Validate author input and convert service results to response DTOs."""

    def __init__(self, service: AuthorService) -> None:
        self.service = service

    def create(self, body: dict[str, Any]) -> AuthorDTO:
        dto = self._from_body(body)
        return self._to_dto(self.service.save(dto))

    def get_by_id(self, author_id: int) -> Optional[AuthorDTO]:
        self._validate_id(author_id)
        author = self.service.get_by_id(author_id)
        if author is None:
            raise ResourceNotFoundError(code="author_not_found", message="The author does not exist.")
        return self._to_dto(author)

    def get_all(self) -> list[AuthorDTO]:
        return [self._to_dto(author) for author in self.service.get_all()]

    def get_by_name(self, name: str) -> Optional[AuthorDTO]:
        self._validate_text(name, "name")
        author = self.service.get_by_name(name)
        if author is None:
            raise ResourceNotFoundError(code="author_not_found", message="The author does not exist.")
        return self._to_dto(author)

    def search_by_name(self, text: str) -> list[AuthorDTO]:
        self._validate_text(text, "text")
        return [self._to_dto(author) for author in self.service.search_by_name(text)]

    def get_with_books(self, author_id: int) -> Optional[AuthorDTO]:
        self._validate_id(author_id)
        author = self.service.get_with_books(author_id)
        if author is None:
            raise ResourceNotFoundError(code="author_not_found", message="The author does not exist.")
        return self._to_dto(author)

    def delete(self, author_id: int) -> bool:
        self._validate_id(author_id)
        if not self.service.delete(author_id):
            raise ResourceNotFoundError(code="author_not_found", message="The author does not exist.")
        return True

    def count(self) -> int:
        return self.service.count()

    @classmethod
    def _from_body(cls, body: dict[str, Any]) -> AuthorDTO:
        cls._require_body(body)
        name = body.get("name")
        nationality = body.get("nationality")
        cls._validate_text(name, "name")
        if nationality is not None:
            cls._validate_text(nationality, "nationality")
        return AuthorDTO(name=name, nationality=nationality)

    @staticmethod
    def _to_dto(author: Optional[Author]) -> Optional[AuthorDTO]:
        if author is None:
            return None
        return AuthorDTO(id=author.id, name=author.name, nationality=author.nationality)

    @staticmethod
    def _require_body(body: Any) -> None:
        if body is None:
            raise ValidationError(code="missing_request_body", message="Request body is required.")
        if not isinstance(body, dict):
            raise ValidationError(code="invalid_request_body", message="Request body must be a JSON object.")

    @staticmethod
    def _validate_id(value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValidationError(code="invalid_id", message="ID must be a positive integer.")

    @staticmethod
    def _validate_text(value: Any, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(code="invalid_field_value", message=f"{field} must be a non-empty string.")
