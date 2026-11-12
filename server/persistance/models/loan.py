from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from book import Book
    from borrower import Borrower


class Loan(Base):
    __tablename__ = "loan"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("book.id", ondelete="CASCADE"), nullable=False
    )
    borrower_id: Mapped[int] = mapped_column(
        ForeignKey("borrower.id", ondelete="CASCADE"), nullable=False
    )
    loan_date: Mapped[dt.date] = mapped_column(
        Date, nullable=False, server_default=text("(CURRENT_DATE)")
    )
    return_date: Mapped[Optional[dt.date]] = mapped_column(Date)

    book: Mapped["Book"] = relationship(back_populates="loans")
    borrower: Mapped["Borrower"] = relationship(back_populates="loans")

    def __repr__(self) -> str:
        return f"Loan(id={self.id!r}, book_id={self.book_id!r}, borrower_id={self.borrower_id!r})"
