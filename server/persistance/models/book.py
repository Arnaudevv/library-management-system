from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from author import Author
    from loan import Loan


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    isbn: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    publication_year: Mapped[Optional[int]]
    author_id: Mapped[int] = mapped_column(
        ForeignKey("author.id", ondelete="CASCADE"), nullable=False
    )

    author: Mapped["Author"] = relationship(back_populates="books")
    loans: Mapped[List["Loan"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Book(id={self.id!r}, title={self.title!r})"
