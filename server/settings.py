"""Network and TLS configuration for the server."""

import os
from pathlib import Path

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
BUFFER_SIZE = 4096

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE_DIR = PROJECT_ROOT / "certs"


def _configured_path(variable: str, default: Path) -> Path:
    value = os.getenv(variable)
    if value is None:
        return default
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


TLS_SERVER_CERT_FILE = _configured_path(
    "TLS_SERVER_CERT_FILE",
    CERTIFICATE_DIR / "server.crt.pem",
)
TLS_SERVER_KEY_FILE = _configured_path(
    "TLS_SERVER_KEY_FILE",
    CERTIFICATE_DIR / "server.key.pem",
)
TLS_CLIENT_CA_FILE = _configured_path(
    "TLS_CLIENT_CA_FILE",
    CERTIFICATE_DIR / "ca.crt.pem",
)
TLS_KEY_PASSWORD = os.getenv("TLS_KEY_PASSWORD") or None
