from __future__ import annotations

from typing import Any

from .response_builder import StatusCode


class ServerError(Exception):
    """Base exception carrying a public error code and HTTP status."""

    status = StatusCode.INTERNAL_SERVER_ERROR
    code = "internal_server_error"
    public_message = "An unexpected server error occurred."
    expose_to_client = True

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: Any | None = None,
    ) -> None:
        self.code = code or self.code
        self.public_message = message or self.public_message
        self.details = details
        super().__init__(self.public_message)


class ProtocolError(ServerError):
    """Represent a malformed HTTP request."""

    status = StatusCode.BAD_REQUEST
    code = "protocol_error"
    public_message = "The request is malformed."


class HeadersTooLargeError(ProtocolError):
    """Represent headers exceeding the configured limit."""

    status = StatusCode.CONTENT_TOO_LARGE
    code = "headers_too_large"
    public_message = "The request headers are too large."


class BodyTooLargeError(ProtocolError):
    """Represent a body exceeding the configured limit."""

    status = StatusCode.CONTENT_TOO_LARGE
    code = "body_too_large"
    public_message = "The request body is too large."


class RoutingError(ServerError):
    """Represent a route matching failure."""

    status = StatusCode.NOT_FOUND
    code = "routing_error"
    public_message = "The requested route was not found."


class RouteNotFoundError(RoutingError):
    """Represent a path with no registered route."""

    code = "route_not_found"


class MethodNotAllowedError(RoutingError):
    """Represent a valid path used with an unsupported method."""

    status = StatusCode.METHOD_NOT_ALLOWED
    code = "method_not_allowed"
    public_message = "The HTTP method is not allowed for this route."


class ValidationError(ServerError):
    """Represent invalid endpoint input."""

    status = StatusCode.BAD_REQUEST
    code = "validation_error"
    public_message = "The request contains invalid input."


class UnsupportedMediaTypeError(ValidationError):
    """Represent an unsupported request content type."""

    status = StatusCode.UNSUPPORTED_MEDIA_TYPE
    code = "unsupported_media_type"
    public_message = "The request media type is not supported."


class UnprocessableContentError(ValidationError):
    """Represent semantically invalid but syntactically valid input."""

    status = StatusCode.UNPROCESSABLE_CONTENT
    code = "unprocessable_content"


class ResourceNotFoundError(ServerError):
    """Represent a requested resource that does not exist."""

    status = StatusCode.NOT_FOUND
    code = "resource_not_found"
    public_message = "The requested resource was not found."


class ConflictError(ServerError):
    """Represent a conflict with application or database state."""

    status = StatusCode.CONFLICT
    code = "business_rule_conflict"
    public_message = "The operation conflicts with the current state."


class DatabaseUnavailableError(ServerError):
    """Represent a temporarily unavailable database."""

    status = StatusCode.SERVICE_UNAVAILABLE
    code = "database_unavailable"
    public_message = "The database is temporarily unavailable."


class DatabaseError(ServerError):
    """Represent an unexpected database failure."""

    status = StatusCode.INTERNAL_SERVER_ERROR
    code = "database_error"
    public_message = "A database error occurred."