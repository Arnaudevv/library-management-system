from __future__ import annotations

from sqlalchemy import select

from server.persistance.database import Base, Session, engine
from server.persistance.models.author import Author
from server.persistance.models.book import Book
from server.persistance.models.borrower import Borrower
from server.persistance.models.loan import Loan


def fill_database() -> None:
    """Create the schema and insert sample library data."""
    Base.metadata.create_all(engine)

    with Session.begin() as session:
        author = session.scalar(select(Author).where(Author.name == "George Orwell"))
        if author is None:
            author = Author(name="George Orwell", nationality="English")
            session.add(author)
            session.flush()

        book = session.scalar(select(Book).where(Book.isbn == "9780451524935"))
        if book is None:
            book = Book(
                title="1984",
                isbn="9780451524935",
                publication_year=1949,
                author=author,
            )
            session.add(book)
            session.flush()

        borrower = session.scalar(select(Borrower).where(Borrower.email == "ada@example.com"))
        if borrower is None:
            borrower = Borrower(name="Ada Lovelace", email="ada@example.com")
            session.add(borrower)
            session.flush()

        loan_exists = session.scalar(
            select(Loan).where(
                Loan.book_id == book.id,
                Loan.borrower_id == borrower.id,
                Loan.return_date.is_(None),
            )
        )
        if loan_exists is None:
            session.add(Loan(book=book, borrower=borrower))


if __name__ == "__main__":
    fill_database()
