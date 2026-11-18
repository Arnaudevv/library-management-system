from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable
from server.persistance.database import Base
from .controllers.author_controller import AuthorController
from .controllers.book_controller import BookController
from .controllers.borrower_controller import BorrowerController
from .controllers.loan_controller import LoanController
from .persistance.config import DATABASE_URL
from .persistance.migrations import migrate_loan_due_date
from .persistance.repositories.unit_of_work import UnitOfWorkFactory
from .protocol.request_reader import Request
from .protocol.errors import (
    MethodNotAllowedError,
    RouteNotFoundError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from .services.author_service import AuthorService
from .services.book_service import BookService
from .services.borrower_service import BorrowerService
from .services.loan_service import LoanService


Handler = Callable[[Request, dict[str, Any]], Any]


@dataclass(frozen=True)
class Route:
    """Describe a route and the controller function it executes."""

    method: str
    pattern: str
    handler: Handler
    converters: dict[str, Callable[[str], Any]]


class Router:
    """Find the controller function that matches a request."""

    def __init__(self, routes: list[Route]) -> None:
        self.routes = routes

    @classmethod
    def create_default(cls) -> Router:
        """Create the application dependencies and register its routes."""
        factory = UnitOfWorkFactory(DATABASE_URL)
        db_file = factory.engine.url.database
        if db_file:
            Path(db_file).parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(factory.engine)
        migrate_loan_due_date(factory.engine)
        authors = AuthorController(AuthorService(factory))
        books = BookController(BookService(factory))
        borrowers = BorrowerController(BorrowerService(factory))
        loans = LoanController(LoanService(factory))

        return cls(
            [
                cls._route("POST", "/authors", lambda request, _: authors.create(cls._json_body(request))),
                cls._route("GET", "/authors", lambda request, _: authors.get_by_name(cls._query(request, "name"))
                    if "name" in request.query
                    else authors.get_all(),
                ),
                cls._route("GET", "/authors/search", lambda request, _: authors.search_by_name(cls._query(request, "text"))),
                cls._route("GET", "/authors/{author_id}/books", lambda _, params: authors.get_with_books(params["author_id"]), {"author_id": int}),
                cls._route("GET", "/authors/{author_id}", lambda _, params: authors.get_by_id(params["author_id"]), {"author_id": int}),
                cls._route("DELETE", "/authors/{author_id}", lambda _, params: authors.delete(params["author_id"]), {"author_id": int}),
                cls._route("POST", "/books", lambda request, _: books.create(cls._json_body(request))),
                cls._route("GET", "/books", lambda request, _: books.get_by_isbn(cls._query(request, "isbn"))
                    if "isbn" in request.query
                    else books.get_all(),
                ),
                cls._route("GET", "/books/search", lambda request, _: books.search_by_title(cls._query(request, "text"))),
                cls._route("GET", "/books/available", lambda _request, _params: books.get_available()),
                cls._route("GET", "/books/with-authors", lambda _request, _params: books.get_all_with_authors()),
                cls._route("GET", "/books/by-author/{author_id}", lambda _, params: books.get_by_author(params["author_id"]), {"author_id": int}),
                cls._route("GET", "/books/{book_id}/loans", lambda _, params: books.get_with_loans(params["book_id"]), {"book_id": int}),
                cls._route("GET", "/books/{book_id}", lambda _, params: books.get_by_id(params["book_id"]), {"book_id": int}),
                cls._route("DELETE", "/books/{book_id}", lambda _, params: books.delete(params["book_id"]), {"book_id": int}),
                cls._route("POST", "/borrowers", lambda request, _: borrowers.create(cls._json_body(request))),
                cls._route("GET", "/borrowers", lambda request, _: borrowers.get_by_email(cls._query(request, "email"))
                    if "email" in request.query
                    else borrowers.get_all(),
                ),
                cls._route("GET", "/borrowers/search", lambda request, _: borrowers.search_by_name(cls._query(request, "text"))),
                cls._route("GET", "/borrowers/{borrower_id}/loans", lambda _, params: borrowers.get_with_loans(params["borrower_id"]), {"borrower_id": int}),
                cls._route("GET", "/borrowers/{borrower_id}", lambda _, params: borrowers.get_by_id(params["borrower_id"]), {"borrower_id": int}),
                cls._route("DELETE", "/borrowers/{borrower_id}", lambda _, params: borrowers.delete(params["borrower_id"]), {"borrower_id": int}),
                cls._route("POST", "/loans", lambda request, _: loans.create(cls._json_body(request))),
                cls._route("POST", "/loans/{loan_id}/return", lambda _, params: loans.return_loan(params["loan_id"]), {"loan_id": int}),
                cls._route("GET", "/loans", lambda _request, _params: loans.get_all()),
                cls._route("GET", "/loans/active", lambda _request, _params: loans.get_active()),
                cls._route("GET", "/loans/history", lambda _request, _params: loans.get_history()),
                cls._route("GET", "/loans/with-relations", lambda _request, _params: loans.get_all_with_relations()),
                cls._route("GET", "/loans/by-book/{book_id}", lambda _, params: loans.get_by_book(params["book_id"]), {"book_id": int}),
                cls._route("GET", "/loans/by-borrower/{borrower_id}", lambda _, params: loans.get_by_borrower(params["borrower_id"]), {"borrower_id": int}),
                cls._route("GET", "/loans/{loan_id}/relations", lambda _, params: loans.get_with_relations(params["loan_id"]), {"loan_id": int}),
                cls._route("GET", "/loans/{loan_id}", lambda _, params: loans.get_by_id(params["loan_id"]), {"loan_id": int}),
                cls._route("DELETE", "/loans/{loan_id}", lambda _, params: loans.delete(params["loan_id"]), {"loan_id": int}),
            ]
        )

    def handle(self, request: Request) -> Any:
        """Execute the controller function registered for a matching request."""
        path_matches = [
            route for route in self.routes if self._path_matches(route.pattern, request.path)
        ]
        for route in self.routes:
            parameters = self._match(route, request)
            if parameters is not None:
                return route.handler(request, parameters)
        if path_matches:
            if any(route.method == request.method for route in path_matches):
                raise ValidationError(
                    code="invalid_path_parameter",
                    message="A path parameter has an invalid value.",
                )
            allowed = ", ".join(sorted({route.method for route in path_matches}))
            raise MethodNotAllowedError(
                message="The HTTP method is not allowed for this route.",
                details={"allow": allowed},
            )
        raise RouteNotFoundError()

    @staticmethod
    def _route(
        method: str,
        pattern: str,
        handler: Handler,
        converters: dict[str, Callable[[str], Any]] | None = None,
    ) -> Route:
        return Route(method, pattern, handler, converters or {})

    @staticmethod
    def _match(route: Route, request: Request) -> dict[str, Any] | None:
        if route.method != request.method:
            return None

        pattern_parts = route.pattern.strip("/").split("/")
        path_parts = request.path.strip("/").split("/")
        if len(pattern_parts) != len(path_parts):
            return None

        parameters: dict[str, Any] = {}
        for pattern_part, path_part in zip(pattern_parts, path_parts):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                name = pattern_part[1:-1]
                converter = route.converters.get(name, str)
                try:
                    parameters[name] = converter(path_part)
                except (TypeError, ValueError):
                    return None
            elif pattern_part != path_part:
                return None
        return parameters

    @staticmethod
    def _path_matches(pattern: str, path: str) -> bool:
        pattern_parts = pattern.strip("/").split("/")
        path_parts = path.strip("/").split("/")
        if len(pattern_parts) != len(path_parts):
            return False
        return all(
            pattern_part.startswith("{")
            and pattern_part.endswith("}")
            or pattern_part == path_part
            for pattern_part, path_part in zip(pattern_parts, path_parts)
        )

    @staticmethod
    def _query(request: Request, name: str) -> str:
        if name not in request.query or not request.query[name]:
            raise ValidationError(
                code="missing_query_parameter",
                message=f"The query parameter '{name}' is required.",
            )
        return request.query[name]

    @staticmethod
    def _json_body(request: Request) -> Any:
        content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise UnsupportedMediaTypeError()
        return request.body
