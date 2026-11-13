from __future__ import annotations

from typing import Optional

from ..dto import BookDTO
from ..persistance.repositories.author_repository import AuthorRepository
from ..persistance.models.book import Book
from ..persistance.repositories.book_repository import BookRepository
from ..persistance.repositories.unit_of_work import UnitOfWorkFactory
from ..protocol.errors import ConflictError, ResourceNotFoundError


class BookService:
    """Apply book business rules and coordinate book repositories."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def get_by_id(self, book_id: int) -> Optional[Book]:
        with self.uow_factory.create() as uow:
            return BookRepository(uow.session).get_by_id(book_id)

    def get_all(self) -> list[Book]:
        with self.uow_factory.create() as uow:
            return BookRepository(uow.session).get_all()

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        with self.uow_factory.create() as uow:
            return BookRepository(uow.session).get_by_isbn(isbn)

    def search_by_title(self, text: str) -> list[Book]:
        with self.uow_factory.create() as uow:
            return BookRepository(uow.session).search_by_title(text)

    def get_by_author(self, author_id: int) -> list[Book]:
        with self.uow_factory.create() as uow:
            return BookRepository(uow.session).get_by_author(author_id)

    def get_all_with_authors(self) -> list[Book]:
        with self.uow_factory.create() as uow:
            return BookRepository(uow.session).get_all_with_authors()

    def get_with_loans(self, book_id: int) -> Optional[Book]:
        with self.uow_factory.create() as uow:
            return BookRepository(uow.session).get_with_loans(book_id)

    def get_available(self) -> list[Book]:
        with self.uow_factory.create() as uow:
            return BookRepository(uow.session).get_available()

    def save(self, book: BookDTO) -> Book:
        with self.uow_factory.create() as uow:
            author_repository = AuthorRepository(uow.session)
            if author_repository.get_by_id(book.author_id) is None:
                raise ResourceNotFoundError(
                    code="author_not_found",
                    message="The author does not exist.",
                )
            repository = BookRepository(uow.session)
            if book.isbn is not None and repository.get_by_isbn(book.isbn) is not None:
                raise ConflictError(
                    code="isbn_already_exists",
                    message="A book with this ISBN already exists.",
                )
            entity = Book(
                title=book.title,
                isbn=book.isbn,
                publication_year=book.publication_year,
                author_id=book.author_id,
            )
            saved = repository.save(entity)
            uow.session.flush()
            return saved

    def delete(self, book_id: int) -> bool:
        with self.uow_factory.create() as uow:
            repository = BookRepository(uow.session)
            book = repository.get_by_id(book_id)
            if book is None:
                return False
            repository.delete(book)
            return True

    def count(self) -> int:
        with self.uow_factory.create() as uow:
            return BookRepository(uow.session).count()
