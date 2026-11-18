# Security: TLS, Client Certificates, and Digests

This project protects communication between a client and the library server.
It uses TLS, client certificates, and SHA-256 body digests.

## What is protected

### TLS and mutual TLS

TLS encrypts data while it travels between the client and the server. It also
lets the client check that it is talking to the expected server.

This project uses **mutual TLS (mTLS)**: the server also asks the client for a
certificate. The server accepts certificates signed by the project's
development CA. A client without a trusted certificate cannot make an HTTPS
connection to the server.

The certificates are created for local development by
[`scripts/generate_certs.py`](../scripts/generate_certs.py). The script creates
a CA, a server identity, two trusted client identities, and an untrusted
identity for rejection tests. It asks you to choose a password for the CA key
and `.p12` files. Keep the generated `certs/` folder local; do not commit or
share private keys.

TLS handles encryption. The application does not implement its own AES
encryption or key exchange.

### SHA-256 body digests

For REST requests, the client sends an `X-Content-Digest` header containing the
SHA-256 digest of the exact request body. The server checks it before routing
the request. Every server response also includes a digest, and the browser's
[`http.js`](../client/js/api/http.js) checks API response digests before
parsing JSON.

A digest is not encryption or a digital signature. TLS provides the protected
connection; the digest is an additional check that the body received by the
application matches the body that was sent.

Browser-managed requests for HTML, CSS, JavaScript, and other static files do
not pass through `http.js`, so the browser cannot add a request digest to them.
The server exempts those static requests from the request-digest requirement.
Static responses still have a digest.

## Why the browser proxy exists

With direct mTLS, the browser must have a trusted CA certificate and a client
certificate installed in its certificate store. That is inconvenient or
blocked on managed university computers. Browser JavaScript cannot load a
private key from the project folder and attach it to the TLS handshake.

The optional [`tools/browser_proxy.py`](../tools/browser_proxy.py) avoids that
installation step. The browser connects to a local proxy, and the proxy uses
the project's `client1` certificate to connect to the server:

```text
Browser --(HTTP on 127.0.0.1)--> Local proxy
        --(HTTPS with mTLS)----> Library server
```

The proxy forwards the browser's request and response digest headers without
recalculating them. It also checks every response digest from the server. A
bad or missing digest produces a `502` response.

### Important proxy limitation

The browser-to-proxy connection is plain HTTP, limited to this computer's
loopback address. Only the proxy-to-server connection is protected by TLS.
The server authenticates the proxy's `client1` certificate, not the browser
or the person using it. Other local software on the same computer may be able
to connect to the proxy.

This proxy is an optional development and demonstration convenience. It does
not replace direct browser mTLS, the Python client, or the security tests. It
also changes the original design in which the browser itself was the mTLS
client, so check that this option is acceptable for the assignment.

## Start the application with the proxy

The following steps use PowerShell on Windows. Run commands from the repository
root. The server entry point in this repository is `run_server.py`.

1. Create and activate a virtual environment, then install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

   In Git Bash, activate the environment with:

   ```bash
   python -m venv .venv
   source .venv/Scripts/activate
   ```

2. Make sure a root-level `.env` file contains:

   ```dotenv
   DEVELOPEMENT_DB=sqlite
   ```

   The spelling `DEVELOPEMENT_DB` is the name the current application reads.

3. Create the SQLite data folder and load the sample data:

   ```powershell
   New-Item -ItemType Directory -Force data | Out-Null
   python -m tests.fill_database
   ```

   The folder is needed before the seed command opens `data/library.db`.

4. Generate development certificates once on this computer:

   ```powershell
   python scripts\generate_certs.py
   ```

   Choose and confirm a password when prompted. If the local `certs/` folder
   already contains generated certificates, skip this step. No certificate
   needs to be installed in Windows or the browser when using the proxy. In
   Git Bash, use `python scripts/generate_certs.py`.

5. Start the server in one terminal:

   ```powershell
   python run_server.py
   ```

6. Start the proxy in a second terminal, from the repository root:

   ```powershell
   python tools\browser_proxy.py
   ```

7. Open **http://localhost:9000** in the browser. Use `http`, not `https`, for
   the local proxy address.

In Git Bash, use forward slashes in the script commands, for example
`python tools/browser_proxy.py`.

## Other ways to test the security layer

The Python demo client uses `client2` directly and does not need a browser
certificate store:

```powershell
python tools\secure_client.py --path /books
```

Run the automated security and application tests with:

```powershell
python -m pytest -q
```

Tests create temporary certificates. They check trusted and rejected clients,
TLS negotiation, request and response digests, the browser proxy, and concurrent
requests.

## Configuration and troubleshooting

The server uses `HOST` and `PORT` from `.env`, defaulting to `127.0.0.1` and
`8000`. The proxy always listens on `127.0.0.1`; its port defaults to `9000`
and can be changed with `BROWSER_PROXY_PORT` or `--port`. It uses the server
host and port by default. `BROWSER_PROXY_SERVER_HOST` and
`BROWSER_PROXY_SERVER_PORT` can override the upstream address.

The proxy's CA, client certificate, and key default to
`certs/ca.crt.pem`, `certs/client1.crt.pem`, and `certs/client1.key.pem`.
Override them with `BROWSER_PROXY_CA_FILE`,
`BROWSER_PROXY_CLIENT_CERT_FILE`, and `BROWSER_PROXY_CLIENT_KEY_FILE` if
needed. Relative paths are resolved from the repository root.

- If SQLite reports `unable to open database file`, create `data/` and rerun
  `python -m tests.fill_database`.
- If the browser cannot connect, check that both the server and proxy are
  running, then open `http://localhost:9000`.
- Do not use `ssl._create_unverified_context()` or disable TLS certificate
  verification.
