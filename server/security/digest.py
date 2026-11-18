from __future__ import annotations

import hashlib
import hmac

from server.protocol.errors import CommunicationIntegrityError


DIGEST_HEADER = "x-content-digest"


def compute_digest(body: bytes) -> str:
    """Return the SHA-256 digest of the exact message body bytes."""
    return hashlib.sha256(body).hexdigest()


def verify_digest(body: bytes, received_digest: str | None) -> None:
    """Reject a missing or incorrect SHA-256 body digest."""
    if received_digest is None:
        raise CommunicationIntegrityError(
            code="digest_missing",
            message="The X-Content-Digest header is required.",
        )

    expected_digest = compute_digest(body)
    if not hmac.compare_digest(expected_digest, received_digest.strip().lower()):
        raise CommunicationIntegrityError(
            code="digest_mismatch",
            message="The request body digest does not match.",
        )
