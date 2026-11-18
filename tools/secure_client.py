from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import ssl
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


async def request(
    host: str,
    port: int,
    path: str,
    ca_file: Path,
    certificate_file: Path,
    private_key_file: Path,
) -> tuple[bytes, bytes]:
    """Make one authenticated HTTPS GET and return response headers and body."""
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(ca_file))
    context.load_cert_chain(
        certfile=str(certificate_file),
        keyfile=str(private_key_file),
    )
    reader, writer = await asyncio.open_connection(
        host,
        port,
        ssl=context,
        server_hostname=host,
    )
    digest = hashlib.sha256(b"").hexdigest()
    writer.write(
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Connection: close\r\n"
        f"X-Content-Digest: {digest}\r\n"
        "\r\n".encode("ascii")
    )
    await writer.drain()
    response = await reader.read()
    writer.close()
    await writer.wait_closed()

    headers, separator, body = response.partition(b"\r\n\r\n")
    if not separator:
        raise ConnectionError("The server closed without an HTTP response.")
    response_headers = _parse_headers(headers)
    received_digest = response_headers.get("x-content-digest")
    expected_digest = hashlib.sha256(body).hexdigest()
    if received_digest is None or received_digest.lower() != expected_digest:
        raise ValueError("The response digest is missing or invalid.")
    return headers, body


def _parse_headers(raw_headers: bytes) -> dict[str, str]:
    lines = raw_headers.decode("iso-8859-1").split("\r\n")[1:]
    return {
        name.strip().lower(): value.strip()
        for line in lines
        if ":" in line
        for name, value in [line.split(":", 1)]
    }


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Make a request using a client certificate.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--path", default="/books")
    parser.add_argument("--ca", type=Path, default=ROOT / "certs" / "ca.crt.pem")
    parser.add_argument("--cert", type=Path, default=ROOT / "certs" / "client2.crt.pem")
    parser.add_argument("--key", type=Path, default=ROOT / "certs" / "client2.key.pem")
    return parser.parse_args()


async def main() -> None:
    arguments = _parse_arguments()
    headers, body = await request(
        arguments.host,
        arguments.port,
        arguments.path,
        arguments.ca,
        arguments.cert,
        arguments.key,
    )
    print(headers.decode("iso-8859-1"))
    if body:
        try:
            print(json.dumps(json.loads(body), indent=2))
        except json.JSONDecodeError:
            print(body.decode("utf-8"))


if __name__ == "__main__":
    asyncio.run(main())
