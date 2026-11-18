from __future__ import annotations

import asyncio
from itertools import count
from time import perf_counter
from typing import Any

from server.error_manager import ErrorManager
from server.protocol.request_reader import MAX_HEADER_SIZE, Request, read_request
from server.protocol.response_builder import Response, StatusCode, build_response
from server.router import Router
from server.security.digest import verify_digest
from server.security.tls import build_server_ssl_context
from server.settings import HOST, PORT
from server.static_files import serve_static


LISTEN_BACKLOG = 5
active_connections = 0
request_ids = count(1)
router: Router | None = None


async def handle_connection(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    """Handle one client request and close its connection gracefully."""
    global active_connections

    active_connections += 1
    request_id = next(request_ids)
    started_at = perf_counter()
    peer_address = _format_address(writer.get_extra_info("peername"))
    local_address = _format_address(writer.get_extra_info("sockname"))

    try:
        _log_client_identity(writer, request_id)
        request: Request = await read_request(reader)

        print(
            f"[REQUEST] {peer_address} "
            f"{request.method} {request.path} "
            f"request_id={request_id} active_connections={active_connections}",
            flush=True,
        )

        response = serve_static(request.path, request.method)
        if response is None:
            verify_digest(
                request.raw_body,
                request.headers.get("x-content-digest"),
            )
            if router is None:
                raise RuntimeError("The application router has not been initialized.")
            response = Response(status=StatusCode.OK, body=router.handle(request))

        writer.write(build_response(response))
        await writer.drain()

        print(
            f"[RESPONSE] {request.method} {request.path} "
            f"{peer_address} -> {local_address} "
            f"request_id={request_id} "
            f"duration_ms={(perf_counter() - started_at) * 1000:.2f} "
            f"active_connections={active_connections}\n",
            flush=True,
        )
        
    except (asyncio.IncompleteReadError, ConnectionError) as error:
        reason = "incomplete_request" if isinstance(error, asyncio.IncompleteReadError) else repr(error)
        print(f"[DISCONNECT] request_id={request_id} peer={peer_address} reason={reason}", flush=True)
        
    except Exception as error:
        print(
            f"[REQUEST ERROR] request_id={request_id} "
            f"duration_ms={(perf_counter() - started_at) * 1000:.2f} "
            f"active_connections={active_connections}",
            flush=True,
        )
        response = ErrorManager.handle(error)
        try:
            writer.write(build_response(response))
            await writer.drain()
        except ConnectionError as disconnect_error:
            print(
                f"[DISCONNECT] request_id={request_id} peer={peer_address} "
                f"reason={disconnect_error!r}",
                flush=True,
            )
            
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionError as error:
            print(
                f"[DISCONNECT] request_id={request_id} peer={peer_address} "
                f"reason={error!r}",
                flush=True,
            )
        finally:
            active_connections -= 1
            print(
                f"[CONNECTIONS] request_id={request_id} "
                f"active_connections={active_connections}"
                f"\n",
                flush=True,
            )


async def socket_listener() -> None:
    """Accept and handle client connections using asyncio streams."""
    global router

    ssl_context = build_server_ssl_context()
    router = Router.create_default()
    server = await asyncio.start_server(
        handle_connection,
        HOST,
        PORT,
        backlog=LISTEN_BACKLOG,
        limit=MAX_HEADER_SIZE + 4,
        ssl=ssl_context,
        ssl_handshake_timeout=10,
    )

    print(
        f"🚀 Secure server is running at https://{HOST}:{PORT}. "
        "Open this URL (changing te proxy port :8000 -> :9000) in your web browser to connect a client.",
        flush=True,
    )

    async with server:
        await server.serve_forever()


def _format_address(address: Any) -> str:
    """Format a stream address as host:port for diagnostic logs."""
    if isinstance(address, tuple) and len(address) >= 2:
        return f"{address[0]}:{address[1]}"
    return str(address)


def _log_client_identity(
    writer: asyncio.StreamWriter,
    request_id: int,
) -> None:
    peer_certificate = writer.get_extra_info("peercert") or {}
    tls_connection = writer.get_extra_info("ssl_object")
    client_name = _certificate_common_name(peer_certificate)
    tls_version = tls_connection.version() if tls_connection else "unknown"
    cipher = tls_connection.cipher() if tls_connection else None
    cipher_name = cipher[0] if cipher else "unknown"
    print(
        f"[AUTH] request_id={request_id} client={client_name} "
        f"tls={tls_version} cipher={cipher_name}",
        flush=True,
    )


def _certificate_common_name(certificate: dict[str, Any]) -> str:
    for relative_distinguished_name in certificate.get("subject", ()):
        for attribute, value in relative_distinguished_name:
            if attribute == "commonName":
                return value
    return "unknown"
