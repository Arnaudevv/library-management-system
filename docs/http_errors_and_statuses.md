# HTTP Errors and Statuses

## Purpose

This document defines the HTTP status codes and error categories for the library server.

The server must return a structured error response instead of silently closing the connection.

The recommended error body is:

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "The requested resource was not found."
  }
}
```

The `code` is stable for clients. The `message` is intended for humans and may change.

## Status code categories

### 2xx success

| Status | Name | Use |
|---|---|---|
| 200 | OK | A read or other operation completed successfully and has a response body. |
| 201 | Created | A resource was created successfully. |
| 204 | No Content | An operation completed successfully without a response body, normally a deletion. |

### 4xx client errors

These errors mean that the client sent an invalid request or requested an invalid operation.

| Status | Name | Use |
|---|---|---|
| 400 | Bad Request | The request cannot be parsed or contains invalid input. |
| 404 | Not Found | The route or requested resource does not exist. |
| 405 | Method Not Allowed | The path exists, but the HTTP method is not supported for it. |
| 409 | Conflict | The request conflicts with the current application or database state. |
| 413 | Content Too Large | The request headers or body exceed the configured size limit. |
| 415 | Unsupported Media Type | The endpoint requires a media type that the request did not provide. |
| 422 | Unprocessable Content | The syntax is valid, but the request fields cannot be accepted by the endpoint. |

### 5xx server errors

These errors mean that the server could not successfully process an otherwise valid request.

| Status | Name | Use |
|---|---|---|
| 500 | Internal Server Error | An unexpected programming or infrastructure error occurred. |
| 503 | Service Unavailable | A required dependency, such as the database, is temporarily unavailable. |

## Protocol errors

Protocol errors originate in `request_reader.py`.

| Error condition | Status | Error code |
|---|---:|---|
| Missing request line | 400 | `malformed_request_line` |
| Request line does not contain method, target, and version | 400 | `malformed_request_line` |
| Unsupported HTTP version | 400 | `unsupported_http_version` |
| Invalid or empty request target | 400 | `invalid_request_target` |
| Malformed header line | 400 | `malformed_header` |
| Empty or invalid header name | 400 | `malformed_header` |
| Duplicate header | 400 | `duplicate_header` |
| Invalid `Content-Length` syntax | 400 | `invalid_content_length` |
| Negative `Content-Length` | 400 | `invalid_content_length` |
| Connection closes before headers are complete | 400 | `incomplete_headers` |
| Connection closes before the body is complete | 400 | `incomplete_body` |
| Body is not valid UTF-8 | 400 | `invalid_body_encoding` |
| Body is not valid JSON when JSON is declared | 400 | `invalid_json` |
| Header size exceeds the configured limit | 413 | `headers_too_large` |
| Body size exceeds the configured limit | 413 | `body_too_large` |

## Routing errors

Routing errors originate in the router.

| Error condition | Status | Error code |
|---|---:|---|
| No registered route matches the path | 404 | `route_not_found` |
| The path exists but does not support the method | 405 | `method_not_allowed` |
| A path parameter cannot be converted to its expected type | 400 | `invalid_path_parameter` |
| A required query parameter is missing | 400 | `missing_query_parameter` |
| A query parameter has an invalid value | 400 | `invalid_query_parameter` |
| Query parameters are mutually incompatible | 400 | `invalid_query_parameters` |

For a `405 Method Not Allowed` response, the server should include an `Allow` header listing the methods supported by the path.

## Controller validation errors

Controller validation errors concern the shape and basic format of endpoint input.

| Error condition | Status | Error code |
|---|---:|---|
| Body is required but missing | 400 | `missing_request_body` |
| Body is not a JSON object | 400 | `invalid_request_body` |
| Required field is missing | 400 | `missing_field` |
| Field has the wrong type | 400 | `invalid_field_type` |
| String is empty when a value is required | 400 | `invalid_field_value` |
| ID is not a positive integer | 400 | `invalid_id` |
| Email format is invalid | 422 | `invalid_email` |
| Date is not a valid ISO date | 400 | `invalid_date` |
| Request content type is not accepted | 415 | `unsupported_media_type` |

The server should not expose Python exception names or tracebacks in these responses.

## Resource errors

Resource errors occur when a requested entity cannot be found.

| Error condition | Status | Error code |
|---|---:|---|
| Author does not exist | 404 | `author_not_found` |
| Book does not exist | 404 | `book_not_found` |
| Borrower does not exist | 404 | `borrower_not_found` |
| Loan does not exist | 404 | `loan_not_found` |

The same status applies when deleting an entity that does not exist.

## Business rule errors

Business rule errors originate in services.

| Error condition | Status | Error code |
|---|---:|---|
| Author name already exists | 409 | `author_already_exists` |
| ISBN already exists | 409 | `isbn_already_exists` |
| Borrower email already exists | 409 | `borrower_already_exists` |
| Book already has an active loan | 409 | `book_already_loaned` |
| Loan cannot be returned in its current state | 409 | `loan_state_conflict` |
| Operation violates a business invariant | 409 | `business_rule_conflict` |

The service should raise specific application exceptions instead of generic `ValueError` instances.

## Persistence errors

Persistence errors originate in SQLAlchemy, the database driver, or the database itself.

| Error condition | Status | Error code |
|---|---:|---|
| Unique constraint violation not caught by the service | 409 | `unique_constraint_violation` |
| Foreign key violation | 409 | `foreign_key_conflict` |
| Non-null constraint violation | 400 | `persistence_validation_error` |
| Transaction rollback | 500 | `transaction_failed` |
| Database connection failure | 503 | `database_unavailable` |
| Database query or driver failure | 500 | `database_error` |

Internal database details must be logged server-side but must not be returned to the client.

## Response-building errors

Response-building errors occur while serializing an application result.

| Error condition | Status | Error code |
|---|---:|---|
| Response body cannot be serialized as JSON | 500 | `response_serialization_error` |
| Invalid response status or header | 500 | `invalid_server_response` |
| A `204` response contains a body | 500 | `invalid_server_response` |

These errors indicate a server implementation problem and should be logged.

## Unexpected errors

Any exception not covered by a known category must produce:

```text
500 Internal Server Error
```

with:

```json
{
  "error": {
    "code": "internal_server_error",
    "message": "An unexpected server error occurred."
  }
}
```

The original exception and traceback must be logged internally. They must not be sent to the client.

## Error handling order

The connection layer should handle errors in this order:

```text
1. Protocol errors
2. Routing errors
3. Controller validation errors
4. Resource errors
5. Business rule errors
6. Persistence errors
7. Unexpected errors
```

Each known exception should be mapped to one documented status and stable error code.

## Current implementation status

The current codebase already defines `ProtocolError` and a small set of successful status codes.

The following work remains:

- Define dedicated application exception classes.
- Add the missing status codes to `StatusCode`.
- Make the router distinguish `404` and `405`.
- Map exceptions to error responses.
- Replace silent exception handling in the connection layer.
- Add tests for each error category.
