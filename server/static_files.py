from __future__ import annotations

import mimetypes
from pathlib import Path

from .protocol.response_builder import Response, StatusCode


CLIENT_ROOT = Path(__file__).resolve().parents[1] / "client"


def serve_static(path: str, method: str) -> Response | None:
    """Return a response for a frontend asset, or None for API routing."""
    if method != "GET":
        return None

    relative_path = "index.html" if path == "/" else path.lstrip("/")
    if not relative_path or "\\" in relative_path:
        return None

    file_path = (CLIENT_ROOT / relative_path).resolve()
    try:
        file_path.relative_to(CLIENT_ROOT.resolve())
    except ValueError:
        return None

    if not file_path.is_file():
        return None

    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    if content_type.startswith("text/") or content_type == "application/javascript":
        content_type = f"{content_type}; charset=utf-8"

    return Response(
        status=StatusCode.OK,
        body=file_path.read_bytes(),
        headers={"content-type": content_type},
    )
