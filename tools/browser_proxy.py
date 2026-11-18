from __future__ import annotations

import argparse
import asyncio
import json
import os
import ssl
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.protocol.errors import CommunicationIntegrityError  # noqa: E402
from server.protocol.request_reader import MAX_HEADER_SIZE  # noqa: E402
from server.security.digest import (  # noqa: E402
    DIGEST_HEADER,
    compute_digest,
    verify_digest,
)


@dataclass(frozen=True)
class ProxyConfig:
    server_host: str
    server_port: int
    ca_file: Path
    client_cert: Path
    client_key: Path


def _path(value: str | None, default: Path) -> Path:
    """Resolve a configured path from the repository root."""
    path = Path(value).expanduser() if value else default
    return path if path.is_absolute() else ROOT / path


async def _read_request(reader: asyncio.StreamReader) -> tuple[bytes, str, str]:
    """Read one request by Content-Length and force upstream connection close."""
    head = await reader.readuntil(b"\r\n\r\n")
    if len(head) > MAX_HEADER_SIZE:
        raise ValueError("Request headers too large.")
    lines = head[:-4].split(b"\r\n")
    parts = lines[0].split()
    if len(parts) != 3 or parts[2] != b"HTTP/1.1":
        raise ValueError("Malformed HTTP/1.1 request line.")
    parsed = [line.partition(b":") for line in lines[1:]]
    if any(not sep for _, sep, _ in parsed) or any(
        name.strip().lower() == b"transfer-encoding" for name, _, _ in parsed
    ):
        raise ValueError("Malformed or unsupported request headers.")
    lengths = [
        value.strip() for name, _, value in parsed
        if name.strip().lower() == b"content-length"
    ]
    if len(lengths) > 1 or (lengths and not lengths[0].isdigit()):
        raise ValueError("Invalid Content-Length.")
    length = int(lengths[0]) if lengths else 0
    if length > MAX_HEADER_SIZE * 64:
        raise ValueError("Request body too large.")
    body = await reader.readexactly(length)
    headers = [
        line for line, (name, _, _) in zip(lines[1:], parsed)
        if name.strip().lower() not in {b"connection", b"proxy-connection"}
    ]
    headers.append(b"Connection: close")
    raw = b"\r\n".join([lines[0], *headers]) + b"\r\n\r\n" + body
    return raw, parts[0].decode("ascii"), parts[1].decode("iso-8859-1")


def _response_parts(response: bytes) -> tuple[int, bytes, str | None]:
    """Extract status, body, and digest from a complete upstream response."""
    head, sep, body = response.partition(b"\r\n\r\n")
    status = head.split(b"\r\n", 1)[0].split()
    if not sep or len(status) < 2 or not status[1].isdigit():
        raise ValueError("Malformed upstream response.")
    digest = next(
        (
            value.strip().decode("ascii")
            for line in head.split(b"\r\n")[1:]
            for name, colon, value in [line.partition(b":")]
            if colon and name.strip().lower() == DIGEST_HEADER.encode("ascii")
        ),
        None,
    )
    return int(status[1]), body, digest


def _error_response(status: int, code: str) -> bytes:
    """Build a digest-bearing JSON error response for the browser."""
    message = "Malformed browser request." if status == 400 else "Secure upstream unavailable."
    body = (
        b'{"code":"digest_mismatch"}'
        if code == "digest_mismatch"
        else json.dumps(
            {"error": {"code": code, "message": message}},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    reason = "Bad Request" if status == 400 else "Bad Gateway"
    return (
        f"HTTP/1.1 {status} {reason}\r\n"
        "Content-Type: application/json; charset=utf-8\r\n"
        f"{DIGEST_HEADER}: {compute_digest(body)}\r\n"
        f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n"
    ).encode("ascii") + body


async def _handle(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    config: ProxyConfig,
    context: ssl.SSLContext,
) -> None:
    """Forward one browser request through the client1 mTLS identity."""
    method = path = "?"
    status, error = 502, None
    tls_version = cipher_name = "unavailable"
    upstream: asyncio.StreamWriter | None = None
    request: bytes | None = None
    try:
        try:
            request, method, path = await _read_request(reader)
            remote, upstream = await asyncio.wait_for(
                asyncio.open_connection(
                    config.server_host, config.server_port, ssl=context,
                    server_hostname=config.server_host, ssl_handshake_timeout=10,
                ),
                15,
            )
            tls = upstream.get_extra_info("ssl_object")
            if tls:
                tls_version = tls.version() or "unknown"
                cipher = tls.cipher()
                cipher_name = cipher[0] if cipher else "unknown"
            upstream.write(request)
            await upstream.drain()
            response = await asyncio.wait_for(remote.read(), 30)
            status, body, digest = _response_parts(response)
            verify_digest(body, digest)
            writer.write(response)
        except CommunicationIntegrityError:
            status, error = 502, "digest_mismatch"
        except (
            OSError,
            ssl.SSLError,
            asyncio.TimeoutError,
            asyncio.IncompleteReadError,
            asyncio.LimitOverrunError,
            ValueError,
        ):
            status = 400 if request is None else 502
            error = "bad_request" if request is None else "upstream_unavailable"
        try:
            if error:
                writer.write(_error_response(status, error))
            await writer.drain()
        except ConnectionError:
            error = error or "client_disconnected"
    finally:
        if upstream:
            upstream.close()
            try:
                await upstream.wait_closed()
            except ConnectionError:
                pass
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionError:
            pass
        print(
            f"[PROXY] method={method!r} path={path!r} status={status} "
            f"identity=client1 tls={tls_version} cipher={cipher_name}"
            f"{f' error={error}' if error else ''}",
            flush=True,
        )


async def start_proxy(config: ProxyConfig, port: int = 9000) -> asyncio.Server:
    """Start the proxy on IPv4 loopback only."""
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(config.ca_file))
    context.load_cert_chain(str(config.client_cert), str(config.client_key))

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await _handle(reader, writer, config, context)

    return await asyncio.start_server(
        handle, "127.0.0.1", port, limit=MAX_HEADER_SIZE + 4
    )


async def _serve(config: ProxyConfig, port: int) -> None:
    """Run the proxy until shutdown."""
    server = await start_proxy(config, port)
    print(f"[PROXY] listening on http://127.0.0.1:{port}", flush=True)
    async with server:
        await server.serve_forever()


def main() -> None:
    """Load project settings and start the browser proxy."""
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Forward browser traffic over mTLS.")
    parser.add_argument("--port", type=int, default=int(os.getenv("BROWSER_PROXY_PORT", "9000")))
    parser.add_argument("--server-host")
    parser.add_argument("--server-port", type=int)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535.")

    from server import settings

    host = args.server_host or os.getenv("BROWSER_PROXY_SERVER_HOST") or settings.HOST
    if host in {"0.0.0.0", "::"}:
        host = "127.0.0.1"
    config = ProxyConfig(
        host,
        args.server_port or int(os.getenv("BROWSER_PROXY_SERVER_PORT", settings.PORT)),
        _path(os.getenv("BROWSER_PROXY_CA_FILE"), settings.TLS_CLIENT_CA_FILE),
        _path(
            os.getenv("BROWSER_PROXY_CLIENT_CERT_FILE"),
            settings.CERTIFICATE_DIR / "client1.crt.pem",
        ),
        _path(
            os.getenv("BROWSER_PROXY_CLIENT_KEY_FILE"),
            settings.CERTIFICATE_DIR / "client1.key.pem",
        ),
    )
    asyncio.run(_serve(config, args.port))


if __name__ == "__main__":
    main()
