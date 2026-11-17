from __future__ import annotations

import json
import datetime as dt
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import create_engine, inspect

from server.error_manager import ErrorManager
from server.persistance.database import Base
# Import models so SQLAlchemy registers their tables in Base.metadata.
from server.persistance.models.author import Author
from server.persistance.models.book import Book
from server.persistance.models.borrower import Borrower
from server.persistance.models.loan import Loan
from server.persistance.migrations import migrate_loan_due_date
from server.controllers.loan_controller import LoanController
from server.protocol.errors import (
    ConflictError,
    MethodNotAllowedError,
    ResourceNotFoundError,
    RouteNotFoundError,
    ServerError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from server.protocol.request_reader import Request
from server.protocol.response_builder import Response, StatusCode, build_response
import server.router as router_module
from server.router import Router


@pytest.fixture
def router(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Router:
    database_url = f"sqlite:///{tmp_path / 'server-flow.db'}"
    schema_engine = create_engine(database_url)
    Base.metadata.create_all(schema_engine)
    monkeypatch.setattr(router_module, "DATABASE_URL", database_url)
    application_router = Router.create_default()
    schema_engine.dispose()
    return application_router


def request(method: str, path: str, body=None, json_body: bool = False) -> Request:
    parsed = urlsplit(path)
    headers = {"content-type": "application/json"} if json_body else {}
    query = {
        key: values[0]
        for key, values in parse_qs(parsed.query, keep_blank_values=True).items()
    }
    return Request(
        method=method,
        path=parsed.path,
        query=query,
        headers=headers,
        body=body,
    )


def create_author(router: Router, name: str = "Jane Austen") -> object:
    return router.handle(
        request(
            "POST",
            "/authors",
            {"name": name, "nationality": "English"},
            json_body=True,
        )
    )


def create_book(router: Router, author_id: int, isbn: str = "isbn-1") -> object:
    return router.handle(
        request(
            "POST",
            "/books",
            {
                "title": "Pride and Prejudice",
                "author_id": author_id,
                "isbn": isbn,
                "publication_year": 1813,
            },
            json_body=True,
        )
    )


def create_borrower(router: Router) -> object:
    return router.handle(
        request(
            "POST",
            "/borrowers",
            {"name": "Ada Lovelace", "email": "ada@example.com"},
            json_body=True,
        )
    )


def create_loan(router: Router, book_id: int, borrower_id: int) -> object:
    return router.handle(
        request(
            "POST",
            "/loans",
            {
                "book_id": book_id,
                "borrower_id": borrower_id,
                "due_date": (dt.date.today() + dt.timedelta(days=14)).isoformat(),
            },
            json_body=True,
        )
    )


def test_author_create_list_filter_and_get(router: Router) -> None:
    author = create_author(router)

    assert author.name == "Jane Austen"
    assert router.handle(request("GET", "/authors")) == [author]
    assert router.handle(request("GET", "/authors?name=Jane Austen")) == author
    assert router.handle(request("GET", "/authors/search?text=austen")) == [author]
    assert router.handle(request("GET", f"/authors/{author.id}")) == author


def test_author_relations_and_delete(router: Router) -> None:
    author = create_author(router)
    book = create_book(router, author.id)

    assert router.handle(request("GET", f"/authors/{author.id}/books")) == author
    assert router.handle(request("DELETE", f"/authors/{author.id}")) is True
    assert router.handle(request("GET", "/authors")) == []


def test_book_queries(router: Router) -> None:
    author = create_author(router)
    book = create_book(router, author.id)

    assert book.author_name == author.name
    assert router.handle(request("GET", "/books")) == [book]
    assert router.handle(request("GET", "/books?isbn=isbn-1")) == book
    assert router.handle(request("GET", "/books/search?text=pride")) == [book]
    assert router.handle(request("GET", "/books/available")) == [book]
    assert router.handle(request("GET", "/books/with-authors")) == [book]
    assert router.handle(request("GET", f"/books/by-author/{author.id}")) == [book]


def test_book_relations_and_delete(router: Router) -> None:
    author = create_author(router)
    book = create_book(router, author.id)

    assert router.handle(request("GET", f"/books/{book.id}/loans")) == book
    assert router.handle(request("DELETE", f"/books/{book.id}")) is True
    assert router.handle(request("GET", "/books")) == []


def test_borrower_create_queries_and_delete(router: Router) -> None:
    borrower = create_borrower(router)

    assert router.handle(request("GET", "/borrowers")) == [borrower]
    assert router.handle(request("GET", "/borrowers?email=ada@example.com")) == borrower
    assert router.handle(request("GET", "/borrowers/search?text=lovelace")) == [borrower]
    assert router.handle(request("GET", f"/borrowers/{borrower.id}")) == borrower
    assert router.handle(request("DELETE", f"/borrowers/{borrower.id}")) is True


def test_loan_create_active_history_and_relations(router: Router) -> None:
    author = create_author(router)
    book = create_book(router, author.id)
    borrower = create_borrower(router)
    loan = create_loan(router, book.id, borrower.id)

    assert router.handle(request("GET", "/loans/active")) == [loan]
    assert router.handle(request("GET", "/loans/history")) == []
    assert router.handle(request("GET", "/loans/with-relations")) == [loan]
    assert router.handle(request("GET", f"/loans/{loan.id}/relations")) == loan
    assert router.handle(request("GET", f"/loans/by-book/{book.id}")) == [loan]
    assert router.handle(request("GET", f"/loans/by-borrower/{borrower.id}")) == [loan]
    assert router.handle(request("GET", "/loans")) == [loan]
    assert loan.book_title == book.title
    assert loan.borrower_name == borrower.name
    assert loan.loan_date == dt.date.today()
    assert loan.due_date == dt.date.today() + dt.timedelta(days=14)


def test_loan_return_moves_loan_to_history(router: Router) -> None:
    author = create_author(router)
    book = create_book(router, author.id)
    borrower = create_borrower(router)
    loan = create_loan(router, book.id, borrower.id)

    returned_loan = router.handle(request("POST", f"/loans/{loan.id}/return"))

    assert returned_loan.id == loan.id
    assert returned_loan.return_date == dt.date.today()
    assert router.handle(request("GET", "/loans/active")) == []
    assert router.handle(request("GET", "/loans/history")) == [returned_loan]

    with pytest.raises(ConflictError, match="already been returned"):
        router.handle(request("POST", f"/loans/{loan.id}/return"))


def test_loan_create_requires_due_date(router: Router) -> None:
    author = create_author(router)
    book = create_book(router, author.id)
    borrower = create_borrower(router)

    with pytest.raises(ValidationError, match="due_date is required"):
        router.handle(
            request(
                "POST",
                "/loans",
                {"book_id": book.id, "borrower_id": borrower.id},
                json_body=True,
            )
        )


def test_loan_due_date_migration_is_idempotent(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'old-loan-schema.db'}")
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "CREATE TABLE loan (id INTEGER PRIMARY KEY, return_date DATE)"
            )

        migrate_loan_due_date(engine)
        migrate_loan_due_date(engine)

        columns = {column["name"] for column in inspect(engine).get_columns("loan")}
        assert "due_date" in columns
    finally:
        engine.dispose()


def test_loan_dto_handles_missing_legacy_relations() -> None:
    loan = Loan(
        id=1,
        book_id=999,
        borrower_id=1,
        loan_date=dt.date.today(),
        borrower=Borrower(id=1, name="Ada Lovelace", email="ada@example.com"),
    )

    dto = LoanController._to_dto(loan)

    assert dto.book_title is None
    assert dto.borrower_name == "Ada Lovelace"


def test_loan_duplicate_active_book_is_rejected(router: Router) -> None:
    author = create_author(router)
    book = create_book(router, author.id)
    first_borrower = create_borrower(router)
    second_borrower = router.handle(
        request(
            "POST",
            "/borrowers",
            {"name": "Grace Hopper", "email": "grace@example.com"},
            json_body=True,
        )
    )
    create_loan(router, book.id, first_borrower.id)

    with pytest.raises(ConflictError, match="active loan"):
        create_loan(router, book.id, second_borrower.id)


def test_request_and_response_json_round_trip() -> None:
    body = {"name": "Jane Austen"}
    response = build_response(
        Response(status=StatusCode.OK, body=body)
    )

    assert response.startswith(b"HTTP/1.1 200 OK\r\n")
    assert json.dumps(body).encode() in response


def test_error_manager_returns_public_response(capsys: pytest.CaptureFixture[str]) -> None:
    response = ErrorManager.handle(
        ResourceNotFoundError(code="book_not_found", message="The book does not exist.")
    )

    assert response.status == StatusCode.NOT_FOUND
    assert response.body["error"]["code"] == "book_not_found"
    assert response.body["error"]["message"] == "The book does not exist."
    assert "exposed_to_client=True" in capsys.readouterr().out


def test_error_manager_hides_unknown_error(capsys: pytest.CaptureFixture[str]) -> None:
    response = ErrorManager.handle(RuntimeError("database password"))

    assert response.status == StatusCode.INTERNAL_SERVER_ERROR
    assert response.body["error"]["code"] == "internal_server_error"
    assert "database password" not in build_response(response).decode()
    assert "exposed_to_client=False" in capsys.readouterr().out


def test_route_not_found_is_typed(router: Router) -> None:
    with pytest.raises(RouteNotFoundError):
        router.handle(request("GET", "/does-not-exist"))


def test_method_not_allowed_is_typed(router: Router) -> None:
    with pytest.raises(MethodNotAllowedError):
        router.handle(request("PATCH", "/authors"))


def test_invalid_path_parameter_is_typed(router: Router) -> None:
    with pytest.raises(ValidationError, match="path parameter"):
        router.handle(request("GET", "/authors/not-an-id"))


@pytest.mark.parametrize(
    ("path", "query"),
    [
        ("/authors", {}),
        ("/books", {}),
        ("/borrowers", {}),
    ],
)
def test_missing_collection_query_is_typed(
    router: Router, path: str, query: dict[str, str]
) -> None:
    if path == "/authors":
        query = {"name": ""}
    elif path == "/books":
        query = {"isbn": ""}
    else:
        query = {"email": ""}

    with pytest.raises(ValidationError, match="query parameter"):
        router.handle(Request(method="GET", path=path, query=query))


def test_unsupported_media_type_is_typed(router: Router) -> None:
    with pytest.raises(UnsupportedMediaTypeError):
        router.handle(request("POST", "/authors", {"name": "Author"}))


@pytest.mark.parametrize(
    "body",
    [None, [], {"nationality": "English"}, {"name": ""}],
)
def test_invalid_author_bodies_are_typed(router: Router, body) -> None:
    with pytest.raises(ValidationError):
        router.handle(request("POST", "/authors", body, json_body=True))


def test_invalid_ids_and_missing_resources_are_typed(router: Router) -> None:
    with pytest.raises(ValidationError, match="positive integer"):
        router.handle(request("GET", "/authors/0"))

    with pytest.raises(ResourceNotFoundError, match="author"):
        router.handle(request("GET", "/authors/999"))


def test_duplicate_author_is_typed_as_conflict(router: Router) -> None:
    create_author(router)

    with pytest.raises(ConflictError):
        create_author(router)


def test_missing_loan_dependencies_are_typed(router: Router) -> None:
    with pytest.raises(ResourceNotFoundError, match="book"):
        create_loan(router, book_id=999, borrower_id=999)


def test_private_known_error_uses_generic_response(capsys: pytest.CaptureFixture[str]) -> None:
    error = ServerError(code="private_detail", message="private")
    error.expose_to_client = False

    response = ErrorManager.handle(error)

    assert response.status == StatusCode.INTERNAL_SERVER_ERROR
    assert response.body["error"]["code"] == "internal_server_error"
    assert "private" not in build_response(response).decode()
    assert "exposed_to_client=False" in capsys.readouterr().out
