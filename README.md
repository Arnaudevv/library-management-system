# Library Management System

A small library application for managing books, authors, borrowers, and loans.
The browser client is built with HTML, CSS, and vanilla JavaScript; the Python
server provides the API and serves the client from the same origin.

> This README describes the synchronous server version before the asyncio
> concurrency refactor.

## Features

- Browse, search, create, and delete books, authors, and borrowers.
- Create loans, view all, active, or returned loans, and return books.
- View a borrower's loan history.

## Architecture

The synchronous TCP server accepts a connection, reads one HTTP request,
dispatches it through the router, controllers, services, repositories, and
SQLAlchemy persistence layer, sends the response, and closes the connection.
It handles connections sequentially: it finishes one request before handling
the next. Socket and database operations are synchronous.

## Requirements

- Python 3.10 or later
- Dependencies listed in `requirements.txt`

The frontend has no separate build step or npm dependencies.

## Getting Started

From the repository root, create and activate a virtual environment, then
install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the repository root with:

```dotenv
DEVELOPEMENT_DB=sqlite
```

The environment variable name above matches the spelling currently read by the
application. This configures the SQLite database at `data/library.db`.

Create the database schema and insert sample data:

```powershell
python -m tests.fill_database
```

Start the server:

```powershell
python run_server.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser. The server
serves both the frontend and API; no separate frontend server is needed.

Run the test suite with:

```powershell
python -m pytest -q
```

## Detailed Documentation

The `docs/` directory contains the full technical documentation. This README is
only a quick introduction and setup guide.

- [HTTP API requests and routes](docs/api_requests.md)
- [API response formats and examples](docs/api_responses.md)
- [HTTP protocol and application layers](docs/protocol.md)
- [HTTP errors and status codes](docs/http_errors_and_statuses.md)
- [Repository queries and persistence notes](docs/repository_queries.md)
- [Async server architecture](docs/async_server.md) documents the later
  concurrency refactor, not the synchronous version described in this README.
