# API Responses

## Raw format received by the client

The server does not send Python objects (`DTO`) to the browser. It converts the DTO to JSON,
encodes it as UTF-8, and sends it inside an HTTP response.

A real response has this structure:

```http
HTTP/1.1 200 OK
content-type: application/json; charset=utf-8
content-length: 58
connection: close

{"name": "Jane Austen", "nationality": "English", "id": 1}
```

The response is divided into:

```text
status line
headers
blank line
JSON body
```

The blank line separates the headers from the body. The value of `content-length`
indicates the size of the body in bytes. The body is the JSON the client must
interpret; it does not include the HTTP headers.

For a list, the raw response would be:

```http
HTTP/1.1 200 OK
content-type: application/json; charset=utf-8
content-length: 60
connection: close

[{"name": "Jane Austen", "nationality": "English", "id": 1}]
```

The spaces and line breaks in the example are only there to show the HTTP
separation. The server serializes the JSON on a single line.

## Documented responses

The following examples show the **JSON body** of each response. To get the
full HTTP response, wrap that body with the status line and headers from the
previous example.

## Author

An author is returned like this:

```json
{
  "name": "Jane Austen",
  "nationality": "English",
  "id": 1
}
```

### `POST /authors`

Returns the created author:

```json
{
  "name": "Jane Austen",
  "nationality": "English",
  "id": 1
}
```

### `GET /authors`

Returns a list:

```json
[
  {
    "name": "Jane Austen",
    "nationality": "English",
    "id": 1
  }
]
```

### `GET /authors/{author_id}`

Returns an author:

```json
{
  "name": "Jane Austen",
  "nationality": "English",
  "id": 1
}
```

### `GET /authors?name={name}`

Returns an author:

```json
{
  "name": "Jane Austen",
  "nationality": "English",
  "id": 1
}
```

### `GET /authors/search?text={text}`

Returns a list of authors whose `name` contains the text:

```json
[
  {
    "name": "Jane Austen",
    "nationality": "English",
    "id": 1
  }
]
```

### `GET /authors/{author_id}/books`

Returns the author in the same flat format. It currently does not include a list of books:

```json
{
  "name": "Jane Austen",
  "nationality": "English",
  "id": 1
}
```

### `DELETE /authors/{author_id}`

Returns a boolean:

```json
true
```

## Book

A book is returned like this:

```json
{
  "title": "Pride and Prejudice",
  "author_id": 1,
  "author_name": "Jane Austen",
  "isbn": "9780141439518",
  "publication_year": 1813,
  "id": 1
}
```

### `POST /books`

Returns the created book:

```json
{
  "title": "Pride and Prejudice",
  "author_id": 1,
  "author_name": "Jane Austen",
  "isbn": "9780141439518",
  "publication_year": 1813,
  "id": 1
}
```

### `GET /books`

Returns a list:

```json
[
  {
    "title": "Pride and Prejudice",
    "author_id": 1,
    "author_name": "Jane Austen",
    "isbn": "9780141439518",
    "publication_year": 1813,
    "id": 1
  }
]
```

### `GET /books/{book_id}`

Returns a book:

```json
{
  "title": "Pride and Prejudice",
  "author_id": 1,
  "author_name": "Jane Austen",
  "isbn": "9780141439518",
  "publication_year": 1813,
  "id": 1
}
```

### `GET /books?isbn={isbn}`

Returns a book:

```json
{
  "title": "Pride and Prejudice",
  "author_id": 1,
  "author_name": "Jane Austen",
  "isbn": "9780141439518",
  "publication_year": 1813,
  "id": 1
}
```

### `GET /books/search?text={text}`

Returns a list of books whose `title` contains the text:

```json
[
  {
    "title": "Pride and Prejudice",
    "author_id": 1,
    "author_name": "Jane Austen",
    "isbn": "9780141439518",
    "publication_year": 1813,
    "id": 1
  }
]
```

### `GET /books/available`

Returns a list of available books:

```json
[
  {
    "title": "Pride and Prejudice",
    "author_id": 1,
    "author_name": "Jane Austen",
    "isbn": "9780141439518",
    "publication_year": 1813,
    "id": 1
  }
]
```

### `GET /books/with-authors`

Returns a list of books in the same flat format. It currently does not include an `author` object:

```json
[
  {
    "title": "Pride and Prejudice",
    "author_id": 1,
    "author_name": "Jane Austen",
    "isbn": "9780141439518",
    "publication_year": 1813,
    "id": 1
  }
]
```

### `GET /books/by-author/{author_id}`

Returns a list of books:

```json
[
  {
    "title": "Pride and Prejudice",
    "author_id": 1,
    "author_name": "Jane Austen",
    "isbn": "9780141439518",
    "publication_year": 1813,
    "id": 1
  }
]
```

### `GET /books/{book_id}/loans`

Returns the book in the same flat format. It currently does not include a list of loans:

```json
{
  "title": "Pride and Prejudice",
  "author_id": 1,
  "author_name": "Jane Austen",
  "isbn": "9780141439518",
  "publication_year": 1813,
  "id": 1
}
```

### `DELETE /books/{book_id}`

```json
true
```

## Borrower

A borrower is returned like this:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "id": 1
}
```

### `POST /borrowers`

Returns the created borrower:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "id": 1
}
```

### `GET /borrowers`

Returns a list:

```json
[
  {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "id": 1
  }
]
```

### `GET /borrowers/{borrower_id}`

Returns a borrower:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "id": 1
}
```

### `GET /borrowers?email={email}`

Returns a borrower:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "id": 1
}
```

### `GET /borrowers/search?text={text}`

Returns a list of borrowers whose `name` contains the text:

```json
[
  {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "id": 1
  }
]
```

### `GET /borrowers/{borrower_id}/loans`

Returns the borrower in the same flat format. It currently does not include a list of loans:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "id": 1
}
```

### `DELETE /borrowers/{borrower_id}`

```json
true
```

## Loan

A loan includes its IDs, the borrower's name, the book's title, the start date, the expected return date and, if it has already been returned, the actual return date.

```json
{
  "book_id": 1,
  "borrower_id": 1,
  "book_title": "Animal Farm",
  "borrower_name": "Ada Lovelace",
  "loan_date": "2026-11-14",
  "due_date": "2026-11-28",
  "return_date": null,
  "id": 1
}
```

`loan_date` is set by the backend when the loan is created. `return_date` is `null` until the book is returned; `due_date` represents the expected date and does not close the loan.

### `POST /loans`

The body requires `book_id`, `borrower_id` and `due_date`:

```json
{
  "book_id": 1,
  "borrower_id": 1,
  "due_date": "2026-11-28"
}
```

Returns the created loan:

```json
{
  "book_id": 1,
  "borrower_id": 1,
  "book_title": "Animal Farm",
  "borrower_name": "Ada Lovelace",
  "loan_date": "2026-11-14",
  "due_date": "2026-11-28",
  "return_date": null,
  "id": 1
}
```

### `GET /loans`

Returns all loans, with their book and borrower data:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "book_title": "Animal Farm",
    "borrower_name": "Ada Lovelace",
    "loan_date": "2026-11-14",
    "due_date": "2026-11-28",
    "return_date": null,
    "id": 1
  }
]
```

### `GET /loans/{loan_id}`

Returns a loan:

```json
{
  "book_id": 1,
  "borrower_id": 1,
  "book_title": "Animal Farm",
  "borrower_name": "Ada Lovelace",
  "loan_date": "2026-11-14",
  "due_date": "2026-11-28",
  "return_date": null,
  "id": 1
}
```

### `GET /loans/by-book/{book_id}`

Returns a list of loans:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "book_title": "Animal Farm",
    "borrower_name": "Ada Lovelace",
    "loan_date": "2026-11-14",
    "due_date": "2026-11-28",
    "return_date": null,
    "id": 1
  }
]
```

### `GET /loans/by-borrower/{borrower_id}`

Returns a list of loans:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "book_title": "Animal Farm",
    "borrower_name": "Ada Lovelace",
    "loan_date": "2026-11-14",
    "due_date": "2026-11-28",
    "return_date": null,
    "id": 1
  }
]
```

### `GET /loans/active`

Returns a list of loans whose `return_date` is `null`:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "book_title": "Animal Farm",
    "borrower_name": "Ada Lovelace",
    "loan_date": "2026-11-14",
    "due_date": "2026-11-28",
    "return_date": null,
    "id": 1
  }
]
```

### `GET /loans/history`

Returns a list of loans whose `return_date` is not `null`:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "book_title": "Animal Farm",
    "borrower_name": "Ada Lovelace",
    "loan_date": "2026-11-01",
    "due_date": "2026-11-14",
    "return_date": "2026-11-14",
    "id": 1
  }
]
```

### `POST /loans/{loan_id}/return`

Records the actual return date in the backend and returns the updated loan:

```json
{
  "book_id": 1,
  "borrower_id": 1,
  "book_title": "Animal Farm",
  "borrower_name": "Ada Lovelace",
  "loan_date": "2026-11-14",
  "due_date": "2026-11-28",
  "return_date": "2026-11-20",
  "id": 1
}
```

### `GET /loans/with-relations`

Returns a list of loans in the same flat format:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "book_title": "Animal Farm",
    "borrower_name": "Ada Lovelace",
    "loan_date": "2026-11-14",
    "due_date": "2026-11-28",
    "return_date": null,
    "id": 1
  }
]
```

### `GET /loans/{loan_id}/relations`

Returns a loan in the same flat format:

```json
{
  "book_id": 1,
  "borrower_id": 1,
  "book_title": "Animal Farm",
  "borrower_name": "Ada Lovelace",
  "loan_date": "2026-11-14",
  "due_date": "2026-11-28",
  "return_date": null,
  "id": 1
}
```

### `DELETE /loans/{loan_id}`

```json
true
```

## Errors

Public errors are returned with this structure:

```json
{
  "error": {
    "code": "author_not_found",
    "message": "The author does not exist."
  }
}
```

An internal error is returned like this:

```json
{
  "error": {
    "code": "internal_server_error",
    "message": "An unexpected server error occurred."
  }
}
```