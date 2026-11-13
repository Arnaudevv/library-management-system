from __future__ import annotations

from typing import Optional

from ..dto import AuthorDTO
from ..persistance.models.author import Author
from ..persistance.repositories.author_repository import AuthorRepository
from ..persistance.repositories.unit_of_work import UnitOfWorkFactory
from ..protocol.errors import ConflictError


class AuthorService:
    """Apply author business rules and coordinate author repositories."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def get_by_id(self, author_id: int) -> Optional[Author]:
        with self.uow_factory.create() as uow:
            return AuthorRepository(uow.session).get_by_id(author_id)

    def get_all(self) -> list[Author]:
        with self.uow_factory.create() as uow:
            return AuthorRepository(uow.session).get_all()

    def get_by_name(self, name: str) -> Optional[Author]:
        with self.uow_factory.create() as uow:
            return AuthorRepository(uow.session).get_by_name(name)

    def search_by_name(self, text: str) -> list[Author]:
        with self.uow_factory.create() as uow:
            return AuthorRepository(uow.session).search_by_name(text)

    def get_with_books(self, author_id: int) -> Optional[Author]:
        with self.uow_factory.create() as uow:
            return AuthorRepository(uow.session).get_with_books(author_id)

    def save(self, author: AuthorDTO) -> Author:
        with self.uow_factory.create() as uow:
            repository = AuthorRepository(uow.session)
            if repository.get_by_name(author.name) is not None:
                raise ConflictError(
                    code="author_already_exists",
                    message="An author with this name already exists.",
                )
            entity = Author(name=author.name, nationality=author.nationality)
            saved = repository.save(entity)
            uow.session.flush()
            return saved

    def delete(self, author_id: int) -> bool:
        with self.uow_factory.create() as uow:
            repository = AuthorRepository(uow.session)
            author = repository.get_by_id(author_id)
            if author is None:
                return False
            repository.delete(author)
            return True

    def count(self) -> int:
        with self.uow_factory.create() as uow:
            return AuthorRepository(uow.session).count()
