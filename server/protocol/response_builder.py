from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict, dataclass, is_dataclass
from enum import IntEnum
from typing import Any


class StatusCode(IntEnum):
    """Define the HTTP status codes used by the application."""

    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    CONTENT_TOO_LARGE = 413
    UNSUPPORTED_MEDIA_TYPE = 415
    UNPROCESSABLE_CONTENT = 422
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


@dataclass
class Response:
    """Represent an application response before HTTP serialization."""

    status: StatusCode
    body: Any | None = None
    headers: dict[str, str] | None = None


def build_response(response: Response) -> bytes:
    """Serialize a Response into an HTTP/1.1 response as UTF-8 bytes."""
    status = _validate_status(response.status)
    headers = _validate_headers(response.headers or {})

    if status == StatusCode.NO_CONTENT and response.body is not None:
        raise ValueError("A 204 response cannot contain a body")

    body = b"" if response.body is None else _serialize_body(response.body)
    if body and "content-type" not in headers:
        headers["content-type"] = "application/json; charset=utf-8"
    headers["content-length"] = str(len(body))
    headers.setdefault("connection", "close")

    reason = _reason_phrase(status)
    header_lines = "".join(
        f"{name}: {value}\r\n" for name, value in headers.items()
    )
    return (
        f"HTTP/1.1 {status.value} {reason}\r\n"
        f"{header_lines}\r\n"
    ).encode("ascii") + body


def _validate_status(status: StatusCode) -> StatusCode:
    """Validate and normalize the response status code."""
    if not isinstance(status, StatusCode):
        raise ValueError("Response status must be a StatusCode")
    return status


def _validate_headers(headers: dict[str, str]) -> dict[str, str]:
    """Validate response header names and values."""
    validated: dict[str, str] = {}
    for name, value in headers.items():
        if not name or "\r" in name or "\n" in name:
            raise ValueError("Response header names cannot contain line breaks")
        if "\r" in value or "\n" in value:
            raise ValueError("Response header values cannot contain line breaks")
        validated[name.lower()] = value
    return validated


def _serialize_body(body: Any) -> bytes:
    """Serialize supported response values as UTF-8 JSON bytes."""
    if isinstance(body, bytes):
        return body

    try:
        return json.dumps(_to_json_compatible(body)).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("Response body is not JSON serializable") from error


def _to_json_compatible(value: Any) -> Any:
    """Convert nested DTOs and supported values into JSON-compatible values."""
    if is_dataclass(value) and not isinstance(value, type):
        return _to_json_compatible(asdict(value))

    if isinstance(value, dict):
        return {
            key: _to_json_compatible(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_to_json_compatible(item) for item in value]

    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()

    return value


def _reason_phrase(status: StatusCode) -> str:
    """Return the standard reason phrase for a supported status code."""
    return {
        StatusCode.OK: "OK",
        StatusCode.CREATED: "Created",
        StatusCode.NO_CONTENT: "No Content",
        StatusCode.BAD_REQUEST: "Bad Request",
        StatusCode.NOT_FOUND: "Not Found",
        StatusCode.METHOD_NOT_ALLOWED: "Method Not Allowed",
        StatusCode.CONFLICT: "Conflict",
        StatusCode.CONTENT_TOO_LARGE: "Content Too Large",
        StatusCode.UNSUPPORTED_MEDIA_TYPE: "Unsupported Media Type",
        StatusCode.UNPROCESSABLE_CONTENT: "Unprocessable Content",
        StatusCode.INTERNAL_SERVER_ERROR: "Internal Server Error",
        StatusCode.SERVICE_UNAVAILABLE: "Service Unavailable",
    }[status]