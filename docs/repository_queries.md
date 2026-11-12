# Repository Queries by Entity

Queries available per entity in the library project (`Author`, `Book`, `Borrower`, `Loan`).
All repositories inherit from `BaseRepository`.

## Common Queries (`BaseRepository`)

Available in all four repositories.

| Method | Description |
|---|---|
| `get_by_id(id)` | Get one row by primary key |
| `get_all()` | Get all rows |
| `save(entity)` | Create or update a row (runs `flush`) |
| `delete(entity)` | Delete a row |
| `count()` | Count rows |

## Author

`name` is not UNIQUE, `nationality` is optional.

| Method | Description | Rule |
|---|---|---|
| `search_by_name(text)` | Authors whose name contains the text (`ilike`) | 2 |
| `get_by_nationality(nationality)` | Authors of a given nationality | 3 |
| `get_with_books(id)` | Author with books loaded (`selectinload`) | 5 |

## Book

`isbn` is UNIQUE, `author_id` is a FK to `author`.

| Method | Description | Rule |
|---|---|---|
| `get_by_isbn(isbn)` | Book by ISBN | 1 |
| `search_by_title(text)` | Books whose title contains the text | 2 |
| `get_by_year(year)` | Books by publication year | 3 |
| `get_by_author(author_id)` | Books of an author | 4 |
| `get_available()` | Books with no active loan (no loan with `return_date` null) | 6 |
| `get_all_with_author()` | Book list with the author loaded | 7 |
| `get_with_loans(id)` | Book with its loan history loaded | 5 |

## Borrower

`email` is UNIQUE.

| Method | Description | Rule |
|---|---|---|
| `get_by_email(email)` | Borrower by email | 1 |
| `search_by_name(text)` | Borrowers whose name contains the text | 2 |
| `get_with_loans(id)` | Borrower with loans loaded | 5 |

## Loan

`return_date` is optional (null = still active). FKs to `book` and `borrower`.

| Method | Description | Rule |
|---|---|---|
| `get_by_book(book_id)` | Loan history of a book | 4 |
| `get_by_borrower(borrower_id)` | Loan history of a borrower | 4 |
| `get_active()` | All loans not yet returned | 6 |
| `get_active_by_book(book_id)` | Current loan of a book (`Optional`) | 6 |
| `get_active_by_borrower(borrower_id)` | Unreturned loans of a borrower | 6 |
| `get_all_with_details()` | Loan list with book and borrower loaded | 7 |

Returning a book needs no method: set `return_date` and call `save`.

## Rules Reference

| Rule | Meaning |
|---|---|
| 1 | UNIQUE field → `get_by_<field>` returning `Optional[T]` |
| 2 | Searchable text field → `search_by_<field>` with `ilike` |
| 3 | Simple filter field (year, status, date) → one filter |
| 4 | Each FK → child-side query `get_by_<parent>(parent_id)` |
| 5 | Each 1:N relation → parent with children loaded (`selectinload`) |
| 6 | State or date attributes → active / history / available queries |
| 7 | Lists showing data from another table → variant loading that relation |

## Notes

1. **Cascades depend on SQLite settings.** The models use `ondelete="CASCADE"` with `passive_deletes=True`, so the database handles child deletion. SQLite does not enforce foreign keys by default; `PRAGMA foreign_keys=ON` is required on the engine.
2. **Nothing prevents two active loans for the same book.** "Book already loaned" is a service-layer rule. A partial unique index on `book_id` where `return_date IS NULL` would let the database enforce it. This is also the race condition to demo in the multi-client step.
3. **`Loan` is not a pure N:M table.** It has its own id and dates, so the same borrower can borrow the same book several times. `get_by_book` returns a history, not a single link.
