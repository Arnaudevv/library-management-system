# Respuestas de la API

## Formato crudo que recibe el cliente

El servidor no envía objetos Python (`DTO`) al navegador. Convierte el DTO a JSON,
lo codifica como UTF-8 y lo envía dentro de una respuesta HTTP.

Una respuesta real tiene esta estructura:

```http
HTTP/1.1 200 OK
content-type: application/json; charset=utf-8
content-length: 58
connection: close

{"name": "Jane Austen", "nationality": "English", "id": 1}
```

La respuesta se divide en:

```text
línea de estado
cabeceras
línea vacía
cuerpo JSON
```

La línea vacía separa las cabeceras del cuerpo. El valor de `content-length`
indica el tamaño del cuerpo en bytes. El cuerpo es el JSON que debe interpretar
el cliente; no incluye las cabeceras HTTP.

Para una lista, el cuerpo crudo sería:

```http
HTTP/1.1 200 OK
content-type: application/json; charset=utf-8
content-length: 60
connection: close

[{"name": "Jane Austen", "nationality": "English", "id": 1}]
```

El espacio y los saltos de línea del ejemplo son únicamente para mostrar la
separación HTTP. El servidor serializa el JSON en una sola línea.

## Respuestas documentadas

Los siguientes ejemplos muestran el **cuerpo JSON** de cada respuesta. Para
obtener la respuesta HTTP completa, hay que envolver ese cuerpo con la línea de
estado y las cabeceras del ejemplo anterior.

## Author

Un autor se devuelve así:

```json
{
  "name": "Jane Austen",
  "nationality": "English",
  "id": 1
}
```

### `POST /authors`

Devuelve el autor creado:

```json
{
  "name": "Jane Austen",
  "nationality": "English",
  "id": 1
}
```

### `GET /authors`

Devuelve una lista:

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

Devuelve un autor:

```json
{
  "name": "Jane Austen",
  "nationality": "English",
  "id": 1
}
```

### `GET /authors?name={name}`

Devuelve un autor:

```json
{
  "name": "Jane Austen",
  "nationality": "English",
  "id": 1
}
```

### `GET /authors/search?text={text}`

Devuelve una lista de autores cuyo `name` contiene el texto:

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

Devuelve el autor con el mismo formato plano. Actualmente no incluye una lista de libros:

```json
{
  "name": "Jane Austen",
  "nationality": "English",
  "id": 1
}
```

### `DELETE /authors/{author_id}`

Devuelve un booleano:

```json
true
```

## Book

Un libro se devuelve así:

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

Devuelve el libro creado:

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

Devuelve una lista:

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

Devuelve un libro:

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

Devuelve un libro:

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

Devuelve una lista de libros cuyo `title` contiene el texto:

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

Devuelve una lista de libros disponibles:

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

Devuelve una lista de libros con el mismo formato plano. Actualmente no incluye un objeto `author`:

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

Devuelve una lista de libros:

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

Devuelve el libro con el mismo formato plano. Actualmente no incluye una lista de préstamos:

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

Un borrower se devuelve así:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "id": 1
}
```

### `POST /borrowers`

Devuelve el borrower creado:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "id": 1
}
```

### `GET /borrowers`

Devuelve una lista:

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

Devuelve un borrower:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "id": 1
}
```

### `GET /borrowers?email={email}`

Devuelve un borrower:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "id": 1
}
```

### `GET /borrowers/search?text={text}`

Devuelve una lista de borrowers cuyo `name` contiene el texto:

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

Devuelve el borrower con el mismo formato plano. Actualmente no incluye una lista de préstamos:

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

Un préstamo se devuelve así:

```json
{
  "book_id": 1,
  "borrower_id": 1,
  "loan_date": "2026-11-14",
  "return_date": null,
  "id": 1
}
```

`return_date` es `null` mientras el préstamo siga activo.

### `POST /loans`

Devuelve el préstamo creado:

```json
{
  "book_id": 1,
  "borrower_id": 1,
  "loan_date": "2026-11-14",
  "return_date": null,
  "id": 1
}
```

### `GET /loans`

Devuelve una lista:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "loan_date": "2026-11-14",
    "return_date": null,
    "id": 1
  }
]
```

### `GET /loans/{loan_id}`

Devuelve un préstamo:

```json
{
  "book_id": 1,
  "borrower_id": 1,
  "loan_date": "2026-11-14",
  "return_date": null,
  "id": 1
}
```

### `GET /loans/by-book/{book_id}`

Devuelve una lista de préstamos:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "loan_date": "2026-11-14",
    "return_date": null,
    "id": 1
  }
]
```

### `GET /loans/by-borrower/{borrower_id}`

Devuelve una lista de préstamos:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "loan_date": "2026-11-14",
    "return_date": null,
    "id": 1
  }
]
```

### `GET /loans/active`

Devuelve una lista de préstamos cuyo `return_date` es `null`:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "loan_date": "2026-11-14",
    "return_date": null,
    "id": 1
  }
]
```

### `GET /loans/history`

Devuelve una lista de préstamos cuyo `return_date` no es `null`:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "loan_date": "2026-11-01",
    "return_date": "2026-11-14",
    "id": 1
  }
]
```

### `GET /loans/with-relations`

Devuelve una lista de préstamos con el mismo formato plano. Actualmente no incluye los objetos `book` ni `borrower`:

```json
[
  {
    "book_id": 1,
    "borrower_id": 1,
    "loan_date": "2026-11-14",
    "return_date": null,
    "id": 1
  }
]
```

### `GET /loans/{loan_id}/relations`

Devuelve un préstamo con el mismo formato plano. Actualmente no incluye los objetos `book` ni `borrower`:

```json
{
  "book_id": 1,
  "borrower_id": 1,
  "loan_date": "2026-11-14",
  "return_date": null,
  "id": 1
}
```

### `DELETE /loans/{loan_id}`

```json
true
```

## Errores

Los errores públicos se devuelven con esta estructura:

```json
{
  "error": {
    "code": "author_not_found",
    "message": "The author does not exist."
  }
}
```

Un error interno se devuelve así:

```json
{
  "error": {
    "code": "internal_server_error",
    "message": "An unexpected server error occurred."
  }
}
```
