from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthorDTO:
    """Represent an author at the application boundary."""

    name: str
    nationality: Optional[str] = None
    id: Optional[int] = None


@dataclass
class BookDTO:
    """Represent a book at the application boundary."""

    title: str
    author_id: int
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    id: Optional[int] = None


@dataclass
class BorrowerDTO:
    """Represent a borrower at the application boundary."""

    name: str
    email: str
    id: Optional[int] = None


@dataclass
class LoanDTO:
    """Represent a loan at the application boundary."""

    book_id: int
    borrower_id: int
    loan_date: Optional[dt.date] = None
    return_date: Optional[dt.date] = None
    id: Optional[int] = None
