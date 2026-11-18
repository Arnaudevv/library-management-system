from __future__ import annotations

import asyncio

import pytest

import server.connection as connection_module
from server.protocol.errors import HeadersTooLargeError
from server.protocol.request_reader import MAX_HEADER_SIZE, Request, read_request
from server.security.digest import compute_digest


def test_read_request_parses_streamed_json_request() -> None:
    async def read_from_stream() -> Request:
        reader = asyncio.StreamReader()
        reader.feed_data(
            b"POST /loans?source=test HTTP/1.1\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: 11\r\n\r\n"
            b'{"book": 1}'
        )
        reader.feed_eof()
        return await read_request(reader)

    request = asyncio.run(read_from_stream())

    assert request.method == "POST"
    assert request.path == "/loans"
    assert request.query == {"source": "test"}
    assert request.headers["content-type"] == "application/json"
    assert request.body == {"book": 1}


def test_read_request_rejects_oversized_headers() -> None:
    async def read_from_stream() -> Request:
        reader = asyncio.StreamReader()
        reader.feed_data(
            b"GET / HTTP/1.1\r\nX-Large: "
            + b"a" * MAX_HEADER_SIZE
            + b"\r\n\r\n"
        )
        reader.feed_eof()
        return await read_request(reader)

    with pytest.raises(HeadersTooLargeError):
        asyncio.run(read_from_stream())


def test_server_handles_multiple_open_connections(monkeypatch, capsys) -> None:
    class StubRouter:
        def handle(self, request: Request) -> dict[str, str]:
            return {"path": request.path}

    monkeypatch.setattr(connection_module, "router", StubRouter())
    monkeypatch.setattr(connection_module, "serve_static", lambda _path, _method: None)
    initial_active_connections = connection_module.active_connections

    async def exercise_connections() -> list[bytes]:
        server = await asyncio.start_server(
            connection_module.handle_connection,
            "127.0.0.1",
            0,
            limit=MAX_HEADER_SIZE + 4,
        )
        async with server:
            host, port = server.sockets[0].getsockname()[:2]

            async def connect_with_partial_headers(path: str):
                reader, writer = await asyncio.open_connection(host, port)
                writer.write(
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: localhost\r\n"
                    f"X-Content-Digest: {compute_digest(b'')}\r\n".encode()
                )
                await writer.drain()
                return reader, writer

            clients = await asyncio.gather(
                connect_with_partial_headers("/first"),
                connect_with_partial_headers("/second"),
            )
            await asyncio.sleep(0.02)

            for _, writer in clients:
                writer.write(b"\r\n")
            await asyncio.gather(*(writer.drain() for _, writer in clients))

            responses = await asyncio.gather(
                *(reader.read() for reader, _ in clients)
            )
            for _, writer in clients:
                writer.close()
            await asyncio.gather(*(writer.wait_closed() for _, writer in clients))
            return responses

    responses = asyncio.run(exercise_connections())
    output = capsys.readouterr().out

    assert all(response.startswith(b"HTTP/1.1 200 OK") for response in responses)
    assert "GET /first request_id=" in output
    assert "GET /second request_id=" in output
    assert "active_connections=2" in output
    assert connection_module.active_connections == initial_active_connections


def test_server_cleans_up_after_client_disconnect(monkeypatch, capsys) -> None:
    monkeypatch.setattr(connection_module, "router", object())
    initial_active_connections = connection_module.active_connections

    async def disconnect_before_request_finishes() -> None:
        server = await asyncio.start_server(
            connection_module.handle_connection,
            "127.0.0.1",
            0,
            limit=MAX_HEADER_SIZE + 4,
        )
        async with server:
            host, port = server.sockets[0].getsockname()[:2]
            _, writer = await asyncio.open_connection(host, port)
            writer.write(b"GET /incomplete HTTP/1.1\r\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            await asyncio.sleep(0.02)

    asyncio.run(disconnect_before_request_finishes())
    output = capsys.readouterr().out

    assert "[DISCONNECT]" in output
    assert "active_connections=0" in output
    assert connection_module.active_connections == initial_active_connections
