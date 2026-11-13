from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .errors import BodyTooLargeError, HeadersTooLargeError, ProtocolError
"""Parse and validate the supported HTTP request protocol.

This module validates the request headers, request line, Content-Length,
body completeness, UTF-8 decoding, and JSON syntax when applicable.
"""

CHUNK_SIZE = 4096
MAX_HEADER_SIZE = 16 * 1024


@dataclass
class Request:
    method: str
    path: str
    query: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    body: Any | None = None


def read_request(conn: socket.socket) -> Request:
    """Read and validate one complete request from a client socket."""
    data = _read_headers(conn)
    head, _, body = data.partition(b"\r\n\r\n")

    try:
        head_text = head.decode("iso-8859-1")
    except UnicodeDecodeError as error:
        raise ProtocolError("Request headers are not decodable") from error

    request_line, headers = _parse_head(head_text)
    method, target = _parse_request_line(request_line)
    length = _parse_content_length(headers)

    if length > MAX_HEADER_SIZE * 64:
        raise BodyTooLargeError()
    body = _read_body(conn, body, length)
    parsed_body = _parse_body(body, headers)

    url = urlsplit(target)
    if not url.path:
        raise ProtocolError(
            code="invalid_request_target",
            message="The request target must contain a path.",
        )

    return Request(
        method=method,
        path=url.path,
        query={
            key: values[0]
            for key, values in parse_qs(url.query, keep_blank_values=True).items()
        },
        headers=headers,
        body=parsed_body,
    )


def _read_headers(conn: socket.socket) -> bytes:
    """Read headers until the header terminator and enforce their size limit."""
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(CHUNK_SIZE)
        if not chunk:
            raise ProtocolError(code="incomplete_headers", message="The request headers are incomplete.")
        data += chunk
        if len(data) > MAX_HEADER_SIZE:
            raise HeadersTooLargeError()
    return data


def _parse_head(head: str) -> tuple[str, dict[str, str]]:
    """Validate header syntax and return the request line and normalized headers."""
    lines = head.split("\r\n")
    if not lines or not lines[0]:
        raise ProtocolError(code="malformed_request_line", message="The request line is malformed.")

    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line or ":" not in line:
            raise ProtocolError(code="malformed_header", message="The request contains a malformed header.")
        name, value = line.split(":", 1)
        name = name.strip()
        value = value.strip()
        if not name or any(character.isspace() for character in name):
            raise ProtocolError(code="malformed_header", message="The request contains an invalid header name.")
        normalized_name = name.lower()
        if normalized_name in headers:
            raise ProtocolError(code="duplicate_header", message="The request contains a duplicate header.")
        headers[normalized_name] = value
    return lines[0], headers


def _parse_request_line(request_line: str) -> tuple[str, str]:
    """Validate the HTTP method, request target, and protocol version."""
    parts = request_line.split()
    if len(parts) != 3:
        raise ProtocolError(code="malformed_request_line", message="The request line is malformed.")
    method, target, version = parts
    if not method.isupper() or not target or version != "HTTP/1.1":
        if version != "HTTP/1.1":
            raise ProtocolError(
                code="unsupported_http_version",
                message="The HTTP version is not supported.",
            )
        raise ProtocolError(code="malformed_request_line", message="The request line is malformed.")
    return method, target


def _parse_content_length(headers: dict[str, str]) -> int:
    """Validate Content-Length and return the expected body size."""
    value = headers.get("content-length")
    if value is None:
        return 0
    if not value or not value.isdecimal():
        raise ProtocolError(
            code="invalid_content_length",
            message="Content-Length must be a non-negative integer.",
        )
    return int(value)


def _read_body(conn: socket.socket, body: bytes, length: int) -> bytes:
    """Read exactly the number of body bytes declared by Content-Length."""
    if len(body) > length:
        return body[:length]

    while len(body) < length:
        chunk = conn.recv(min(CHUNK_SIZE, length - len(body)))
        if not chunk:
            raise ProtocolError(code="incomplete_body", message="The request body is incomplete.")
        body += chunk
    return body


def _parse_body(body: bytes, headers: dict[str, str]) -> Any | None:
    """Decode the body as UTF-8 and parse it as JSON when requested."""
    if not body:
        return None

    content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ProtocolError(code="invalid_body_encoding", message="The request body is not valid UTF-8.") from error

    if content_type == "application/json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise ProtocolError(code="invalid_json", message="The request body contains invalid JSON.") from error
    return text
