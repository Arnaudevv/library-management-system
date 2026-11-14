from __future__ import annotations

from typing import Any, Optional

from ..dto import BookDTO
from ..persistance.models.book import Book
from ..protocol.errors import ResourceNotFoundError, ValidationError
from ..services.book_service import BookService


class BookController:
    """Validate book input and convert service results to response DTOs."""

    def __init__(self, service: BookService) -> None:
        self.service = service

    def create(self, body: dict[str, Any]) -> BookDTO:
        return self._to_dto(self.service.save(self._from_body(body)))

    def get_by_id(self, book_id: int) -> Optional[BookDTO]:
        self._validate_id(book_id)
        book = self.service.get_by_id(book_id)
        if book is None:
            raise ResourceNotFoundError(code="book_not_found", message="The book does not exist.")
        return self._to_dto(book)

    def get_all(self) -> list[BookDTO]:
        return [self._to_dto(book) for book in self.service.get_all()]

    def get_by_isbn(self, isbn: str) -> Optional[BookDTO]:
        self._validate_text(isbn, "isbn")
        book = self.service.get_by_isbn(isbn)
        if book is None:
            raise ResourceNotFoundError(code="book_not_found", message="The book does not exist.")
        return self._to_dto(book)

    def search_by_title(self, text: str) -> list[BookDTO]:
        self._validate_text(text, "text")
        return [self._to_dto(book) for book in self.service.search_by_title(text)]

    def get_by_author(self, author_id: int) -> list[BookDTO]:
        self._validate_id(author_id)
        return [self._to_dto(book) for book in self.service.get_by_author(author_id)]

    def get_all_with_authors(self) -> list[BookDTO]:
        return [self._to_dto(book) for book in self.service.get_all_with_authors()]

    def get_with_loans(self, book_id: int) -> Optional[BookDTO]:
        self._validate_id(book_id)
        book = self.service.get_with_loans(book_id)
        if book is None:
            raise ResourceNotFoundError(code="book_not_found", message="The book does not exist.")
        return self._to_dto(book)

    def get_available(self) -> list[BookDTO]:
        return [self._to_dto(book) for book in self.service.get_available()]

    def delete(self, book_id: int) -> bool:
        self._validate_id(book_id)
        if not self.service.delete(book_id):
            raise ResourceNotFoundError(code="book_not_found", message="The book does not exist.")
        return True

    def count(self) -> int:
        return self.service.count()

    @classmethod
    def _from_body(cls, body: dict[str, Any]) -> BookDTO:
        if not isinstance(body, dict):
            if body is None:
                raise ValidationError(code="missing_request_body", message="Request body is required.")
            raise ValidationError(code="invalid_request_body", message="Request body must be a JSON object.")
        title = body.get("title")
        author_id = body.get("author_id")
        isbn = body.get("isbn")
        publication_year = body.get("publication_year")
        cls._validate_text(title, "title")
        cls._validate_id(author_id, "author_id")
        if isbn is not None:
            cls._validate_text(isbn, "isbn")
        if publication_year is not None and (
            not isinstance(publication_year, int) or isinstance(publication_year, bool)
        ):
            raise ValidationError(code="invalid_field_type", message="publication_year must be an integer.")
        return BookDTO(
            title=title,
            author_id=author_id,
            isbn=isbn,
            publication_year=publication_year,
        )

    @staticmethod
    def _to_dto(book: Optional[Book]) -> Optional[BookDTO]:
        if book is None:
            return None
        return BookDTO(
            id=book.id,
            title=book.title,
            author_id=book.author_id,
            author_name=book.author.name,
            isbn=book.isbn,
            publication_year=book.publication_year,
        )

    @staticmethod
    def _validate_id(value: Any, field: str = "ID") -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValidationError(code="invalid_id", message=f"{field} must be a positive integer.")

    @staticmethod
    def _validate_text(value: Any, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(code="invalid_field_value", message=f"{field} must be a non-empty string.")
