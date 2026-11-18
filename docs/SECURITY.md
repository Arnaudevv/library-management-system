# Secure Communication

The asyncio server uses mutual TLS (mTLS) and SHA-256 body digests. The existing
router, controllers, services, repositories, and synchronous SQLAlchemy layer
are unchanged.

## What protects the connection

Before HTTP is handled, TLS authenticates the server and requires a client
certificate issued by the project's CA. TLS negotiates ephemeral session keys
and encrypts traffic with a symmetric cipher. The application does not implement
its own AES key exchange.

REST requests must contain `X-Content-Digest`, the lowercase hexadecimal
SHA-256 of the exact request body bytes. The server verifies it before routing
the request. Every response, including errors and empty responses, contains the
same header computed from the exact serialized body bytes.

The browser's `http.js` wrapper adds request digests and verifies API response
digests before parsing JSON. Browser-managed HTML, CSS, and JavaScript requests
do not pass through that wrapper. They are protected by TLS and receive a digest
header, but the browser does not verify that custom header.

SHA-256 is an unkeyed integrity check, not encryption or sender authentication.
TLS provides confidentiality, peer authentication, and transport integrity.

## Generate development certificates

Install the project's Python dependencies and run this command from the
repository root:

```powershell
python scripts/generate_certs.py
```

The script asks for a password and creates a local `certs/` directory containing:

- A development CA and its encrypted private key.
- A server certificate and private key for `localhost` and `127.0.0.1`.
- Two CA-signed client identities and password-protected `.p12` files.
- A client signed by an untrusted CA for rejection tests.

For access from another device, include the server's DNS name or LAN IP when
generating certificates, for example:

```powershell
python scripts/generate_certs.py --server-name 192.168.1.20
```

The host must also be reachable on the network. Set `HOST=0.0.0.0` in `.env`
when the server should listen on all network interfaces. Use the same DNS name
or IP in the browser URL that was included in the server certificate.

All private keys and `.p12` files are local development credentials and are
ignored by Git. Never commit or publicly share them. Keep `ca.key.pem` only with
the CA operator; clients need the CA certificate, not the CA private key.

## Configure the browser

On the machine running the browser:

1. Import `certs/ca.crt.pem` into the operating system or browser's trusted root
   certificate store. This lets the browser verify the server certificate.
2. Import `certs/client1.p12` into the personal/client certificate store using
   the password entered during generation.
3. Start the server with `python run_server.py`.
4. Open `https://localhost:8000` (or the configured server name/IP). Select the
   client certificate if the browser prompts.

Chrome and Edge on Windows use the Windows certificate store. Firefox may use
its own certificate store depending on its settings. A browser without a
trusted client certificate is rejected during the TLS handshake, before any
HTTP request reaches the application.

For a second client without browser certificate-store setup, use the generated
`client2` PEM files with the Python demonstration client:

```powershell
python tools/secure_client.py --path /books
```

The secure client verifies the server against `ca.crt.pem`, presents
`client2.crt.pem`, sends the request digest, and validates the response digest.

## Configuration

The server uses these environment variables; defaults point to files generated
in the repository's `certs/` directory:

| Variable | Default |
|---|---|
| `HOST` | `127.0.0.1` |
| `PORT` | `8000` |
| `TLS_SERVER_CERT_FILE` | `certs/server.crt.pem` |
| `TLS_SERVER_KEY_FILE` | `certs/server.key.pem` |
| `TLS_CLIENT_CA_FILE` | `certs/ca.crt.pem` |

Relative certificate paths are resolved from the repository root. The server
requires TLS 1.2 or newer and validates client certificates against only the
configured CA. Do not use `ssl._create_unverified_context()` or disable
certificate verification.

## Verification and limitations

Run all tests with:

```powershell
python -m pytest -q
```

Tests generate temporary certificates and cover trusted and rejected clients,
TLS negotiation, request/response digests, and concurrent connections. No
private test keys are stored in the repository.

The digest requirement is applied to REST API requests and responses. Requests
for browser-managed static assets are exempt from the request digest because
the browser cannot add a body digest through the application's `fetch` wrapper.
Static responses still travel over authenticated TLS and include a digest
header, but the browser does not independently verify it.
