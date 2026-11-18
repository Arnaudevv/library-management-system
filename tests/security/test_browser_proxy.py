from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

import pytest

pytest_plugins = ("tests.test_security",)

import server.connection as connection_module
from server.protocol.request_reader import MAX_HEADER_SIZE, Request
from server.security.tls import build_server_ssl_context
from tools.browser_proxy import ProxyConfig, start_proxy


class StubRouter:
    def handle(self, request: Request) -> dict[str, str]:
        return {"path": request.path}


def _config(certificates: Path, *, rogue: bool = False) -> ProxyConfig:
    prefix = "rogue-client" if rogue else "client1"
    return ProxyConfig(
        server_host="127.0.0.1",
        server_port=0,
        ca_file=certificates / "ca.crt.pem",
        client_cert=certificates / f"{prefix}.crt.pem",
        client_key=certificates / f"{prefix}.key.pem",
    )


async def _get(proxy_port: int, path: str = "/authors") -> bytes:
    reader, writer = await asyncio.open_connection("127.0.0.1", proxy_port)
    writer.write(
        f"GET {path} HTTP/1.1\r\n"
        "Host: localhost:9000\r\n"
        f"X-Content-Digest: {hashlib.sha256(b'').hexdigest()}\r\n"
        "Connection: keep-alive\r\n\r\n".encode("ascii")
    )
    await writer.drain()
    response = await reader.read()
    writer.close()
    await writer.wait_closed()
    return response


def _response_parts(response: bytes) -> tuple[bytes, bytes, dict[str, str]]:
    head, _, body = response.partition(b"\r\n\r\n")
    headers = {
        name.strip().lower(): value.strip()
        for line in head.decode("ascii").split("\r\n")[1:]
        for name, value in [line.split(":", 1)]
    }
    return head, body, headers


async def _start_upstream(
    certificates: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    tamper_digest: bool = False,
) -> asyncio.Server:
    if not tamper_digest:
        monkeypatch.setattr(connection_module, "router", StubRouter())
        monkeypatch.setattr(connection_module, "serve_static", lambda _path, _method: None)
        context = build_server_ssl_context(
            certificates / "server.crt.pem",
            certificates / "server.key.pem",
            certificates / "ca.crt.pem",
        )
        return await asyncio.start_server(
            connection_module.handle_connection,
            "127.0.0.1",
            0,
            ssl=context,
            limit=MAX_HEADER_SIZE + 4,
        )

    async def tampered_response(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readuntil(b"\r\n\r\n")
        body = b'{"ok":true}'
        writer.write(
            b"HTTP/1.1 200 OK\r\n"
            b"X-Content-Digest: "
            + b"0" * 64
            + b"\r\nContent-Length: "
            + str(len(body)).encode("ascii")
            + b"\r\nConnection: close\r\n\r\n"
            + body
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    context = build_server_ssl_context(
        certificates / "server.crt.pem",
        certificates / "server.key.pem",
        certificates / "ca.crt.pem",
    )
    return await asyncio.start_server(
        tampered_response,
        "127.0.0.1",
        0,
        ssl=context,
        limit=MAX_HEADER_SIZE + 4,
    )


def test_proxy_forwards_authenticated_request_and_digest(
    certificate_files: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def exercise() -> bytes:
        upstream = await _start_upstream(certificate_files, monkeypatch)
        async with upstream:
            host, port = upstream.sockets[0].getsockname()[:2]
            config = _config(certificate_files)
            proxy = await start_proxy(
                ProxyConfig(**{**config.__dict__, "server_host": host, "server_port": port}),
                0,
            )
            async with proxy:
                return await _get(proxy.sockets[0].getsockname()[1])

    response = asyncio.run(exercise())
    head, body, headers = _response_parts(response)
    assert head.startswith(b"HTTP/1.1 200 OK")
    assert headers["x-content-digest"] == hashlib.sha256(body).hexdigest()
    assert b'"/authors"' in body
    assert "identity=client1 tls=TLSv1." in capsys.readouterr().out


def test_proxy_returns_502_for_rejected_client_and_keeps_serving(
    certificate_files: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def exercise() -> tuple[bytes, bytes, bool]:
        upstream = await _start_upstream(certificate_files, monkeypatch)
        async with upstream:
            host, port = upstream.sockets[0].getsockname()[:2]
            config = _config(certificate_files, rogue=True)
            config = ProxyConfig(**{**config.__dict__, "server_host": host, "server_port": port})
            proxy = await start_proxy(config, 0)
            async with proxy:
                proxy_port = proxy.sockets[0].getsockname()[1]
                first = await _get(proxy_port)
                second = await _get(proxy_port)
                return first, second, proxy.is_serving()

    first, second, serving = asyncio.run(exercise())
    assert first.startswith(b"HTTP/1.1 502 Bad Gateway")
    assert second.startswith(b"HTTP/1.1 502 Bad Gateway")
    assert serving
    assert b"upstream_unavailable" in first


def test_proxy_returns_502_for_tampered_response_digest(
    certificate_files: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def exercise() -> bytes:
        upstream = await _start_upstream(
            certificate_files,
            monkeypatch,
            tamper_digest=True,
        )
        async with upstream:
            host, port = upstream.sockets[0].getsockname()[:2]
            config = _config(certificate_files)
            config = ProxyConfig(**{**config.__dict__, "server_host": host, "server_port": port})
            proxy = await start_proxy(config, 0)
            async with proxy:
                return await _get(proxy.sockets[0].getsockname()[1])

    response = asyncio.run(exercise())
    head, body, headers = _response_parts(response)
    assert head.startswith(b"HTTP/1.1 502 Bad Gateway")
    assert body == b'{"code":"digest_mismatch"}'
    assert headers["x-content-digest"] == hashlib.sha256(body).hexdigest()


def test_proxy_binds_to_loopback_and_handles_concurrent_requests(
    certificate_files: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def exercise() -> tuple[str, list[bytes]]:
        upstream = await _start_upstream(certificate_files, monkeypatch)
        async with upstream:
            host, port = upstream.sockets[0].getsockname()[:2]
            config = _config(certificate_files)
            config = ProxyConfig(**{**config.__dict__, "server_host": host, "server_port": port})
            proxy = await start_proxy(config, 0)
            async with proxy:
                proxy_host, proxy_port = proxy.sockets[0].getsockname()[:2]
                responses = await asyncio.gather(*(_get(proxy_port) for _ in range(8)))
                return proxy_host, responses

    proxy_host, responses = asyncio.run(exercise())
    assert proxy_host == "127.0.0.1"
    assert all(response.startswith(b"HTTP/1.1 200 OK") for response in responses)
