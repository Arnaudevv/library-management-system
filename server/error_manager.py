from __future__ import annotations

import traceback
from typing import Any

from server.protocol.errors import ServerError
from server.protocol.response_builder import Response, StatusCode


class ErrorManager:
    """Classify errors, report them internally, and build public responses."""

    GENERIC_CODE = "internal_server_error"
    GENERIC_MESSAGE = "An unexpected server error occurred."

    @classmethod
    def handle(cls, error: Exception) -> Response:
        """Return the response that can safely be sent to the client."""
        known_error = error if isinstance(error, ServerError) else None
        is_public = known_error is not None and known_error.expose_to_client

        cls._print_error(error, is_public)

        if not is_public:
            return cls._generic_response()

        return Response(
            status=known_error.status,
            body={
                "error": {
                    "code": known_error.code,
                    "message": known_error.public_message,
                }
            },
        )

    @classmethod
    def _print_error(cls, error: Exception, is_public: bool) -> None:
        """Print diagnostic information for the server operator."""
        if isinstance(error, ServerError):
            status = error.status.value
            code = error.code
            public_message = error.public_message
            private_details: Any = error.details
        else:
            status = StatusCode.INTERNAL_SERVER_ERROR.value
            code = cls.GENERIC_CODE
            public_message = cls.GENERIC_MESSAGE
            private_details = repr(error)

        print(
            "[ERROR] "
            f"status={status} "
            f"code={code} "
            f"exposed_to_client={is_public} "
            f"public_message={public_message!r} "
            f"private_details={private_details!r}"
        )

        if not is_public:
            traceback.print_exception(type(error), error, error.__traceback__)

    @classmethod
    def _generic_response(cls) -> Response:
        """Build the safe fallback response for unexpected exceptions."""
        return Response(
            status=StatusCode.INTERNAL_SERVER_ERROR,
            body={
                "error": {
                    "code": cls.GENERIC_CODE,
                    "message": cls.GENERIC_MESSAGE,
                }
            },
        )
