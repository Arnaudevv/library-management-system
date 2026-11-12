# Server and HTTP Protocol

## Purpose

The server implements a small HTTP-like application over TCP sockets without using a web framework.

The server is organized into these layers:

```text
Socket
  -> Request reader
  -> Router
  -> Controller
  -> Service
  -> Repository
  -> Database
```

The response follows the reverse direction:

```text
Database
  -> Repository
  -> Service
  -> Controller
  -> Response
  -> Response builder
  -> Socket
```

## Request reader

`server/protocol/request_reader.py` is responsible for converting raw HTTP bytes into a `Request` object.

It must:

- Read headers until `\r\n\r\n`.
- Validate the request line.
- Validate the basic header syntax.
- Reject duplicate headers.
- Validate `Content-Length`.
- Enforce the configured header and body size limits.
- Read exactly the declared body length.
- Decode the body as UTF-8.
- Parse JSON when `Content-Type` is `application/json`.
- Raise a protocol error when the request is malformed.

The request reader does not know application routes or business rules.

## Request object

A parsed request contains:

```text
method  -> HTTP method, such as GET or POST
path    -> URL path without the query string
query   -> query parameters
headers -> normalized lowercase header names
body    -> parsed JSON, text, or None
```

## Router

`server/router.py` contains the static route table.

The router is responsible only for:

- Matching the HTTP method.
- Matching the URL path.
- Extracting path parameters.
- Converting path parameters to their expected types.
- Executing the controller function registered for the route.

The router must not:

- Access repositories directly.
- Apply business rules.
- Serialize JSON.
- Build raw HTTP bytes.
- Decide how database errors are handled.

Routes are declared explicitly and contain:

```text
HTTP method
path pattern
controller handler
path parameter converters
```

For example:

```text
GET /authors/{author_id}
```

is matched against:

```text
GET /authors/5
```

and produces:

```text
author_id = 5
```

## Controllers

Controllers validate endpoint input and translate between transport data and DTOs.

They are responsible for:

- Reading body, query, and path values supplied by the router.
- Validating required fields and basic types.
- Validating simple formats such as ISO dates and email values.
- Creating input DTOs.
- Calling the appropriate service.
- Converting service entities into response DTOs.

Controllers must not:

- Query repositories directly.
- Manage database sessions.
- Apply multi-step business rules.
- Serialize DTOs into raw HTTP bytes.

## Services

Services implement application use cases and business rules.

They are responsible for:

- Coordinating repositories.
- Creating a Unit of Work.
- Validating business invariants.
- Committing successful transactions.
- Rolling back failed transactions.
- Returning entities or application results to controllers.

Examples of business rules include:

- The referenced author must exist when creating a book.
- ISBN and borrower email values must not conflict.
- A book cannot have more than one active loan.
- A book and borrower must exist before creating a loan.

## Repositories and persistence

Repositories contain SQLAlchemy queries and persistence operations.

The persistence layer is responsible for:

- Loading and storing entities.
- Applying database-level constraints.
- Executing queries through the Unit of Work session.

Database constraints include:

- Required columns.
- Unique ISBN values.
- Unique borrower email values.
- Foreign keys.
- Cascading deletes.

The database remains the final integrity boundary, even when a rule is also checked by a service.

## Response object

The application creates a structured `Response` before serializing it:

```text
status
body
headers
```

The body may contain:

- One DTO.
- A list of DTOs.
- A JSON-compatible dictionary.
- `None`.

The controller returns DTOs. The response builder converts the structured response into HTTP bytes.

## Response builder

`server/protocol/response_builder.py` is responsible for:

- Validating the response status type.
- Validating response header safety.
- Serializing DTOs and JSON-compatible values.
- Converting dates to ISO strings.
- Adding `Content-Type` when a body exists.
- Calculating `Content-Length` in bytes.
- Building the HTTP status line and headers.
- Returning UTF-8 HTTP response bytes.

It must not:

- Query the database.
- Validate business rules.
- Decide whether a resource exists.
- Choose a status based on an exception.

## Connection handling

`server/connection.py` coordinates one request-response cycle:

```text
read_request
  -> router.handle
  -> create Response
  -> build_response
  -> conn.sendall
```

The current server handles one request per connection and closes the connection afterwards.

Connection-level error handling must eventually:

- Convert known protocol and application errors into HTTP responses.
- Log unexpected failures.
- Avoid silently discarding exceptions.
- Close the client connection safely.

## Validation boundaries

```text
Request reader -> HTTP syntax and body decoding
Router         -> method, path, and path parameters
Controller     -> endpoint input shape and basic formats
Service        -> business rules and use cases
Repository     -> database queries
Database       -> persistence integrity
Response builder-> response serialization
```
