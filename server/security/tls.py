from __future__ import annotations

import ssl
from pathlib import Path

from server.settings import (
    TLS_CLIENT_CA_FILE,
    TLS_KEY_PASSWORD,
    TLS_SERVER_CERT_FILE,
    TLS_SERVER_KEY_FILE,
)


def build_server_ssl_context(
    certificate_file: Path = TLS_SERVER_CERT_FILE,
    private_key_file: Path = TLS_SERVER_KEY_FILE,
    client_ca_file: Path = TLS_CLIENT_CA_FILE,
    key_password: str | None = TLS_KEY_PASSWORD,
) -> ssl.SSLContext:
    """Create a TLS context that requires certificates issued by the project CA."""
    context = ssl.create_default_context(
        purpose=ssl.Purpose.CLIENT_AUTH,
        cafile=str(client_ca_file),
    )
    context.load_cert_chain(
        certfile=str(certificate_file),
        keyfile=str(private_key_file),
        password=key_password,
    )
    context.verify_mode = ssl.CERT_REQUIRED
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context
