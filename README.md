# Library Management System

A small web application for managing books, authors, borrowers, and loans.
The browser client uses plain HTML, CSS, and JavaScript. The Python server
serves both the web page and its API.

## Requirements

- Python 3.10 or later
- Git
- No Node.js or frontend build step

## Start the app on Windows

The recommended browser setup uses the local proxy. You do **not** need to
install certificates in Windows or the browser.

### 1. Clone the repository

In PowerShell:

```powershell
git clone https://github.com/Arnaudevv/library-management-system.git
cd library-management-system
```

If you already cloned the repository, open a terminal at its root folder.

### 2. Create a virtual environment and install dependencies

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

In Git Bash, create and activate it with:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### 3. Configure and prepare the database

Create or update a `.env` file in the repository root:

```dotenv
DEVELOPEMENT_DB=sqlite
```

The spelling `DEVELOPEMENT_DB` matches the setting currently read by the
application. Create the data folder, then create the database schema and
sample records:

```powershell
New-Item -ItemType Directory -Force data | Out-Null
python -m tests.fill_database
```

In Git Bash, use `mkdir -p data` instead of `New-Item`.

### 4. Generate local development certificates

Run this once for each fresh clone:

```powershell
python scripts\generate_certs.py
```

Choose and confirm a password when prompted. The generated `certs/` folder
contains local development identities and is not included in Git. If it already
contains certificates, skip this step; the generator does not overwrite them.
In Git Bash, use `python scripts/generate_certs.py`.

### 5. Start the server and proxy

Keep the server running in one terminal:

```powershell
python run_server.py
```

Open a second terminal at the repository root, activate the same virtual
environment, and start the proxy:

```powershell
python tools\browser_proxy.py
```

In Git Bash, use `python tools/browser_proxy.py`. Then open
[http://localhost:9000](http://localhost:9000) in the browser. Use `http` for
this local address, not `https`.

The proxy allows the browser to reach the mTLS server without importing
certificates into the PC. It listens only on `127.0.0.1`. Read
[the security guide](docs/SECURITY.md) for what the proxy changes and its
limitations.

## Run the tests

With the virtual environment active:

```powershell
python -m pytest -q
```

The optional Python client can also make an authenticated API request:

```powershell
python tools\secure_client.py --path /books
```

## Troubleshooting

- **`unable to open database file`:** make sure `data/` exists, then rerun
  `python -m tests.fill_database`.
- **The browser cannot connect:** keep both the server and proxy terminals
  running, and open `http://localhost:9000`.
- **`tools/browser_proxy.py` is missing after cloning:** use a commit or branch
  that contains the proxy.

Press `Ctrl+C` in each terminal to stop the server and proxy.

## Architecture note

The description below is the original synchronous design summary. The current
server uses asyncio; see [the async server guide](docs/async_server.md).

The original design handled connections sequentially: it read one HTTP request,
dispatched it through the router, controllers, services, repositories, and
SQLAlchemy persistence layer, sent the response, and closed the connection.

## More documentation

- [Security setup and browser proxy](docs/SECURITY.md)
- [HTTP API routes and requests](docs/api_requests.md)
- [API response formats](docs/api_responses.md)
- [HTTP protocol and application layers](docs/protocol.md)
- [HTTP errors and status codes](docs/http_errors_and_statuses.md)
- [Repository queries and persistence](docs/repository_queries.md)
