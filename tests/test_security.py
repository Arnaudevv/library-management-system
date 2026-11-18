from __future__ import annotations

import asyncio
import hashlib
import ssl
import sys
from pathlib import Path

import pytest
from cryptography import x509

import server.connection as connection_module
from scripts import generate_certs
from server.protocol.errors import CommunicationIntegrityError
from server.protocol.request_reader import MAX_HEADER_SIZE, Request
from server.protocol.response_builder import Response, StatusCode, build_response
from server.security.digest import compute_digest, verify_digest
from server.security.tls import build_server_ssl_context


@pytest.fixture
def certificate_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    certificate_dir = tmp_path / "certs"
    passwords = iter(("test-password", "test-password"))
    monkeypatch.setattr(
        generate_certs.getpass,
        "getpass",
        lambda _prompt: next(passwords),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_certs.py", "--output-dir", str(certificate_dir)],
    )
    generate_certs.main()
    return certificate_dir


def test_digest_handles_empty_and_utf8_bodies() -> None:
    body = '{"name":"José"}'.encode("utf-8")

    assert compute_digest(b"") == hashlib.sha256(b"").hexdigest()
    verify_digest(body, compute_digest(body))


@pytest.mark.parametrize(
    ("received_digest", "expected_code"),
    [(None, "digest_missing"), ("0" * 64, "digest_mismatch")],
)
def test_digest_rejects_missing_or_invalid_values(
    received_digest: str | None,
    expected_code: str,
) -> None:
    with pytest.raises(CommunicationIntegrityError) as error:
        verify_digest(b"message", received_digest)

    assert error.value.code == expected_code


def test_every_response_contains_digest_for_serialized_bytes() -> None:
    response = build_response(
        Response(
            status=StatusCode.OK,
            body={"message": "olá"},
            headers={"X-Test": "value"},
        )
    )
    raw_headers, body = response.split(b"\r\n\r\n", 1)
    headers = {
        name.lower(): value
        for line in raw_headers.decode("ascii").split("\r\n")[1:]
        for name, value in [line.split(": ", 1)]
    }

    assert headers["x-content-digest"] == hashlib.sha256(body).hexdigest()


def test_tls_accepts_both_ca_signed_clients_and_rejects_others(
    certificate_files: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class StubRouter:
        def handle(self, request: Request) -> dict[str, str]:
            return {"path": request.path}

    monkeypatch.setattr(connection_module, "router", StubRouter())
    monkeypatch.setattr(connection_module, "serve_static", lambda _path, _method: None)
    initial_active = connection_module.active_connections

    async def exercise() -> tuple[list[tuple[bytes, str, str]], list[bytes]]:
        ca_file = certificate_files / "ca.crt.pem"
        server = await asyncio.start_server(
            connection_module.handle_connection,
            "127.0.0.1",
            0,
            ssl=build_server_ssl_context(
                certificate_files / "server.crt.pem",
                certificate_files / "server.key.pem",
                ca_file,
            ),
            limit=MAX_HEADER_SIZE + 4,
        )

        async with server:
            host, port = server.sockets[0].getsockname()[:2]

            async def make_request(
                certificate_name: str | None,
                key_name: str | None,
                server_name: str = "localhost",
            ) -> tuple[bytes, str, str]:
                context = ssl.create_default_context(
                    ssl.Purpose.SERVER_AUTH,
                    cafile=str(ca_file),
                )
                if certificate_name and key_name:
                    context.load_cert_chain(
                        certificate_files / certificate_name,
                        certificate_files / key_name,
                    )

                try:
                    reader, writer = await asyncio.open_connection(
                        host,
                        port,
                        ssl=context,
                        server_hostname=server_name,
                    )
                    tls_connection = writer.get_extra_info("ssl_object")
                    tls_version = tls_connection.version()
                    cipher = tls_connection.cipher()[0]
                    body = b""
                    digest = compute_digest(body)
                    writer.write(
                        "GET /secure-test HTTP/1.1\r\n"
                        "Host: localhost\r\n"
                        f"X-Content-Digest: {digest}\r\n"
                        "\r\n".encode("ascii")
                    )
                    await writer.drain()
                    response = await asyncio.wait_for(reader.read(), timeout=2)
                    writer.close()
                    await writer.wait_closed()
                    return response, tls_version, cipher
                except (OSError, ssl.SSLError, asyncio.IncompleteReadError):
                    return b"", "", ""

            valid_connections = [
                await make_request(f"{client}.crt.pem", f"{client}.key.pem")
                for client in ("client1", "client2")
            ]
            rejected_responses = [
                (await make_request(
                    "rogue-client.crt.pem",
                    "rogue-client.key.pem",
                ))[0],
                (await make_request(None, None))[0],
                (await make_request(
                    "client1.crt.pem",
                    "client1.key.pem",
                    server_name="untrusted.example",
                ))[0],
            ]
            return valid_connections, rejected_responses

    valid_connections, rejected_responses = asyncio.run(exercise())
    output = capsys.readouterr().out

    assert all(
        response.startswith(b"HTTP/1.1 200 OK")
        for response, _, _ in valid_connections
    )
    assert all(
        version in {"TLSv1.2", "TLSv1.3"}
        for _, version, _ in valid_connections
    )
    assert all(
        "GCM" in cipher or "CHACHA20" in cipher
        for _, _, cipher in valid_connections
    )
    assert rejected_responses == [b"", b"", b""]
    assert "client=client1 tls=TLSv1." in output
    assert "client=client2 tls=TLSv1." in output
    assert connection_module.active_connections == initial_active


def test_api_digest_error_is_returned_with_a_valid_response_digest(
    certificate_files: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MustNotReachRouter:
        def handle(self, _request: Request):
            raise AssertionError("Invalid request digest reached the router.")

    monkeypatch.setattr(connection_module, "router", MustNotReachRouter())
    monkeypatch.setattr(connection_module, "serve_static", lambda _path, _method: None)

    async def send_invalid_digest() -> bytes:
        ca_file = certificate_files / "ca.crt.pem"
        server = await asyncio.start_server(
            connection_module.handle_connection,
            "127.0.0.1",
            0,
            ssl=build_server_ssl_context(
                certificate_files / "server.crt.pem",
                certificate_files / "server.key.pem",
                ca_file,
            ),
            limit=MAX_HEADER_SIZE + 4,
        )
        async with server:
            host, port = server.sockets[0].getsockname()[:2]
            context = ssl.create_default_context(
                ssl.Purpose.SERVER_AUTH,
                cafile=str(ca_file),
            )
            context.load_cert_chain(
                certificate_files / "client1.crt.pem",
                certificate_files / "client1.key.pem",
            )
            reader, writer = await asyncio.open_connection(
                host,
                port,
                ssl=context,
                server_hostname="localhost",
            )
            writer.write(
                b"GET /secure-test HTTP/1.1\r\n"
                b"Host: localhost\r\n"
                b"X-Content-Digest: "
                + b"0" * 64
                + b"\r\n\r\n"
            )
            await writer.drain()
            response = await asyncio.wait_for(reader.read(), timeout=2)
            writer.close()
            await writer.wait_closed()
            return response

    response = asyncio.run(send_invalid_digest())
    raw_headers, body = response.split(b"\r\n\r\n", 1)
    headers = {
        name.lower(): value
        for line in raw_headers.decode("ascii").split("\r\n")[1:]
        for name, value in [line.split(": ", 1)]
    }

    assert response.startswith(b"HTTP/1.1 400 Bad Request")
    assert b"digest_mismatch" in body
    assert headers["x-content-digest"] == hashlib.sha256(body).hexdigest()


def test_server_certificate_contains_required_names(certificate_files: Path) -> None:
    certificate = x509.load_pem_x509_certificate(
        (certificate_files / "server.crt.pem").read_bytes()
    )
    subject_alt_names = certificate.extensions.get_extension_for_class(
        x509.SubjectAlternativeName
    ).value

    assert "localhost" in subject_alt_names.get_values_for_type(x509.DNSName)
    assert "127.0.0.1" in [
        str(address)
        for address in subject_alt_names.get_values_for_type(x509.IPAddress)
    ]
