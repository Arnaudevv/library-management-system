from __future__ import annotations

import datetime as dt

from sqlalchemy import select

from server.persistance.database import Base, Session, engine
from server.persistance.models.author import Author
from server.persistance.models.book import Book
from server.persistance.models.borrower import Borrower
from server.persistance.models.loan import Loan


AUTHORS = (
    ("George Orwell", "English"),
    ("Jane Austen", "English"),
    ("Mary Shelley", "English"),
    ("F. Scott Fitzgerald", "American"),
)

BOOKS = (
    ("1984", "9780451524935", 1949, "George Orwell"),
    ("Animal Farm", "9780451526342", 1945, "George Orwell"),
    ("Pride and Prejudice", "9780141439518", 1813, "Jane Austen"),
    ("Emma", "9780141439587", 1815, "Jane Austen"),
    ("Sense and Sensibility", "9780141439662", 1811, "Jane Austen"),
    ("Frankenstein", "9780486282114", 1818, "Mary Shelley"),
    ("The Last Man", "9780199552346", 1826, "Mary Shelley"),
    ("The Great Gatsby", "9780743273565", 1925, "F. Scott Fitzgerald"),
    ("Tender Is the Night", "9780684801544", 1934, "F. Scott Fitzgerald"),
    ("This Side of Paradise", "9780684822304", 1920, "F. Scott Fitzgerald"),
)

BORROWERS = (
    ("Ada Lovelace", "ada@example.com"),
    ("Grace Hopper", "grace@example.com"),
    ("Katherine Johnson", "katherine@example.com"),
    ("Alan Turing", "alan@example.com"),
    ("Linus Torvalds", "linus@example.com"),
)

LOANS = (
    ("Animal Farm", "grace@example.com", dt.date(2026, 1, 10), None),
    ("Pride and Prejudice", "linus@example.com", dt.date(2026, 1, 12), None),
    ("Frankenstein", "katherine@example.com", dt.date(2025, 2, 1), dt.date(2025, 2, 15)),
    ("The Great Gatsby", "ada@example.com", dt.date(2025, 3, 5), dt.date(2025, 3, 19)),
)


def fill_database() -> None:
    """Create the schema and insert sample library data if it is missing."""
    Base.metadata.create_all(engine)

    with Session.begin() as session:
        authors: dict[str, Author] = {}
        for name, nationality in AUTHORS:
            author = session.scalar(select(Author).where(Author.name == name))
            if author is None:
                author = Author(name=name, nationality=nationality)
                session.add(author)
            authors[name] = author
        session.flush()

        books: dict[str, Book] = {}
        for title, isbn, publication_year, author_name in BOOKS:
            book = session.scalar(select(Book).where(Book.isbn == isbn))
            if book is None:
                book = Book(
                    title=title,
                    isbn=isbn,
                    publication_year=publication_year,
                    author=authors[author_name],
                )
                session.add(book)
            books[title] = book
        session.flush()

        borrowers: dict[str, Borrower] = {}
        for name, email in BORROWERS:
            borrower = session.scalar(select(Borrower).where(Borrower.email == email))
            if borrower is None:
                borrower = Borrower(name=name, email=email)
                session.add(borrower)
            borrowers[email] = borrower
        session.flush()

        for title, email, loan_date, return_date in LOANS:
            book = books[title]
            borrower = borrowers[email]
            if return_date is None:
                existing_loan = session.scalar(
                    select(Loan).where(
                        Loan.book_id == book.id,
                        Loan.borrower_id == borrower.id,
                        Loan.return_date.is_(None),
                    )
                )
            else:
                existing_loan = session.scalar(
                    select(Loan).where(
                        Loan.book_id == book.id,
                        Loan.borrower_id == borrower.id,
                        Loan.loan_date == loan_date,
                        Loan.return_date == return_date,
                    )
                )

            if existing_loan is None:
                session.add(
                    Loan(
                        book=book,
                        borrower=borrower,
                        loan_date=loan_date,
                        return_date=return_date,
                    )
                )


if __name__ == "__main__":
    fill_database()
