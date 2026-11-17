from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from server.persistance.database import Base
from server.persistance.models.author import Author
from server.persistance.models.book import Book
from server.persistance.models.borrower import Borrower
from server.persistance.models.loan import Loan
from server.persistance.repositories.author_repository import AuthorRepository
from server.persistance.repositories.book_repository import BookRepository
from server.persistance.repositories.borrower_repository import BorrowerRepository
from server.persistance.repositories.loan_repository import LoanRepository
from server.persistance.repositories.unit_of_work import UnitOfWorkFactory


@pytest.fixture
def factory() -> UnitOfWorkFactory:
    unit_of_work_factory = UnitOfWorkFactory("sqlite:///:memory:")
    Base.metadata.create_all(unit_of_work_factory.engine)
    return unit_of_work_factory


def test_author_repository(factory: UnitOfWorkFactory) -> None:
    with factory.create() as uow:
        repository = AuthorRepository(uow.session)
        author = repository.save(Author(name="Jane Austen", nationality="English"))
        uow.session.flush()
        author_id = author.id

        assert repository.get_by_id(author_id) is author
        assert repository.get_all() == [author]
        assert repository.get_by_name("Jane Austen") is author
        assert repository.get_by_name("Unknown") is None
        assert repository.search_by_name("austen") == [author]
        assert repository.search_by_name("unknown") == []
        assert repository.get_with_books(author_id).books == []
        assert repository.get_with_books(999) is None

        repository.delete(author)
        uow.session.flush()
        assert repository.count() == 0


def test_book_repository(factory: UnitOfWorkFactory) -> None:
    with factory.create() as uow:
        author = AuthorRepository(uow.session).save(Author(name="George Orwell"))
        first = Book(title="Animal Farm", isbn="isbn-1", publication_year=1945, author=author)
        second = Book(title="1984", isbn="isbn-2", publication_year=1949, author=author)
        repository = BookRepository(uow.session)
        repository.save(first)
        repository.save(second)
        uow.session.flush()

        assert repository.get_by_id(first.id) is first
        assert repository.get_all() == [first, second]
        assert repository.get_by_isbn("isbn-1") is first
        assert repository.get_by_isbn("missing") is None
        assert repository.search_by_title("farm") == [first]
        assert repository.search_by_title("missing") == []
        assert repository.get_by_author(author.id) == [first, second]
        assert repository.get_by_author(999) == []
        assert repository.get_all_with_authors()[0].author is author
        assert repository.get_with_loans(first.id).loans == []
        assert repository.get_with_loans(999) is None
        assert repository.get_available() == [first, second]

        repository.delete(first)
        uow.session.flush()
        assert repository.count() == 1


def test_borrower_repository(factory: UnitOfWorkFactory) -> None:
    with factory.create() as uow:
        repository = BorrowerRepository(uow.session)
        borrower = repository.save(Borrower(name="Ada Lovelace", email="ada@example.com"))
        uow.session.flush()

        assert repository.get_by_id(borrower.id) is borrower
        assert repository.get_all() == [borrower]
        assert repository.get_by_email("ada@example.com") is borrower
        assert repository.get_by_email("missing@example.com") is None
        assert repository.search_by_name("lovelace") == [borrower]
        assert repository.search_by_name("missing") == []
        assert repository.get_with_loans(borrower.id).loans == []
        assert repository.get_with_loans(999) is None

        repository.delete(borrower)
        uow.session.flush()
        assert repository.count() == 0


def test_loan_repository(factory: UnitOfWorkFactory) -> None:
    with factory.create() as uow:
        author = AuthorRepository(uow.session).save(Author(name="Author"))
        book = BookRepository(uow.session).save(Book(title="Book", author=author))
        borrower = BorrowerRepository(uow.session).save(
            Borrower(name="Borrower", email="borrower@example.com")
        )
        active = Loan(book=book, borrower=borrower)
        historical = Loan(
            book=book,
            borrower=borrower,
            return_date=dt.date(2026, 1, 1),
        )
        repository = LoanRepository(uow.session)
        repository.save(active)
        repository.save(historical)
        uow.session.flush()

        assert repository.get_by_id(active.id) is active
        assert repository.get_all() == [active, historical]
        assert repository.get_by_book(book.id) == [active, historical]
        assert repository.get_by_borrower(borrower.id) == [active, historical]
        assert repository.get_by_book(999) == []
        assert repository.get_by_borrower(999) == []
        assert repository.get_active() == [active]
        assert repository.get_history() == [historical]
        assert repository.get_all_with_relations()[0].book is book
        assert repository.get_all_with_relations()[0].borrower is borrower
        assert repository.get_with_relations(active.id).book is book
        assert repository.get_with_relations(active.id).borrower is borrower
        assert repository.get_with_relations(999) is None

        repository.delete(active)
        uow.session.flush()
        assert repository.count() == 1
        assert repository.get_active() == []


def test_unique_constraints_raise_on_flush(factory: UnitOfWorkFactory) -> None:
    uow = factory.create()
    try:
        repository = BorrowerRepository(uow.session)
        repository.save(Borrower(name="First", email="same@example.com"))
        repository.save(Borrower(name="Second", email="same@example.com"))

        with pytest.raises(IntegrityError):
            uow.session.flush()
    finally:
        uow.rollback()
        uow.session.close()


def test_sqlite_foreign_keys_are_enabled(factory: UnitOfWorkFactory) -> None:
    with factory.create() as uow:
        assert uow.session.connection().exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_cascade_deletes_books_when_author_is_deleted(factory: UnitOfWorkFactory) -> None:
    with factory.create() as uow:
        author = AuthorRepository(uow.session).save(Author(name="Parent"))
        book = BookRepository(uow.session).save(Book(title="Child", author=author))
        uow.session.flush()
        book_id = book.id
        AuthorRepository(uow.session).delete(author)
        uow.session.flush()

        assert BookRepository(uow.session).get_by_id(book_id) is None
