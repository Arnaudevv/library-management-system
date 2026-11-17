# Async server

The server uses Python's `asyncio.start_server` and stream-based client handlers.
Each connection handles one HTTP request, sends one response, and then closes.
The browser can continue using the same HTTP routes and response formats.

Request bytes are read with `StreamReader` asynchronously. Header, request-line,
and JSON validation remain synchronous because parsing in-memory data does not
wait for I/O. The existing router, controllers, services, and repositories also
remain synchronous.

The server therefore provides concurrency while waiting for network I/O, but it
does not make synchronous SQLAlchemy operations non-blocking. A database call
occupies the event-loop thread until it returns, delaying other handlers during
that operation. This is the chosen initial approach; async SQLAlchemy and an
async SQLite driver are not introduced.

Handlers close their writers in a `finally` block and track active connections.
The existing `[REQUEST]` and `[RESPONSE]` log fields are preserved and extended
with request IDs, active connection counts, and response durations. Disconnects
are logged without stopping the server.
