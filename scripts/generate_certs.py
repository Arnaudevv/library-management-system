from __future__ import annotations

import argparse
import getpass
import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "certs"


def main() -> None:
    """Generate a local development CA, server certificate, and client identities."""
    arguments = _parse_arguments()
    output_dir = arguments.output_dir.resolve()
    _prepare_output_directory(output_dir)
    password = _read_export_password()

    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_certificate = _create_certificate(
        common_name="Library Development CA",
        public_key=ca_key.public_key(),
        issuer_certificate=None,
        issuer_key=ca_key,
        is_ca=True,
    )
    _write_private_key(output_dir / "ca.key.pem", ca_key, password)
    _write_certificate(output_dir / "ca.crt.pem", ca_certificate)

    server_key = ec.generate_private_key(ec.SECP256R1())
    server_certificate = _create_certificate(
        common_name="localhost",
        public_key=server_key.public_key(),
        issuer_certificate=ca_certificate,
        issuer_key=ca_key,
        is_ca=False,
        extended_usage=ExtendedKeyUsageOID.SERVER_AUTH,
        server_names=arguments.server_name,
    )
    _write_identity(output_dir, "server", server_key, server_certificate)

    for client_name in ("client1", "client2"):
        client_key = ec.generate_private_key(ec.SECP256R1())
        client_certificate = _create_certificate(
            common_name=client_name,
            public_key=client_key.public_key(),
            issuer_certificate=ca_certificate,
            issuer_key=ca_key,
            is_ca=False,
            extended_usage=ExtendedKeyUsageOID.CLIENT_AUTH,
        )
        _write_identity(output_dir, client_name, client_key, client_certificate)
        _write_pkcs12(
            output_dir / f"{client_name}.p12",
            client_name,
            client_key,
            client_certificate,
            ca_certificate,
            password,
        )

    rogue_ca_key = ec.generate_private_key(ec.SECP256R1())
    rogue_ca_certificate = _create_certificate(
        common_name="Untrusted Development CA",
        public_key=rogue_ca_key.public_key(),
        issuer_certificate=None,
        issuer_key=rogue_ca_key,
        is_ca=True,
    )
    rogue_key = ec.generate_private_key(ec.SECP256R1())
    rogue_certificate = _create_certificate(
        common_name="unauthorized-client",
        public_key=rogue_key.public_key(),
        issuer_certificate=rogue_ca_certificate,
        issuer_key=rogue_ca_key,
        is_ca=False,
        extended_usage=ExtendedKeyUsageOID.CLIENT_AUTH,
    )
    _write_private_key(output_dir / "rogue-ca.key.pem", rogue_ca_key, password)
    _write_certificate(output_dir / "rogue-ca.crt.pem", rogue_ca_certificate)
    _write_identity(output_dir, "rogue-client", rogue_key, rogue_certificate)
    _write_pkcs12(
        output_dir / "rogue-client.p12",
        "unauthorized-client",
        rogue_key,
        rogue_certificate,
        rogue_ca_certificate,
        password,
    )

    print(f"Development certificates written to: {output_dir}")
    print("Keep all private keys and PKCS#12 files out of version control.")


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated files (must be empty or absent).",
    )
    parser.add_argument(
        "--server-name",
        action="append",
        default=[],
        help="Additional DNS name or IP address used to access the server.",
    )
    arguments = parser.parse_args()
    arguments.server_name.insert(0, "localhost")
    return arguments


def _prepare_output_directory(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"{output_dir} is not empty; choose an empty directory to avoid "
            "overwriting existing keys."
        )
    output_dir.mkdir(parents=True, exist_ok=True)


def _read_export_password() -> bytes:
    password = getpass.getpass("Password for CA key and client .p12 files: ")
    confirmation = getpass.getpass("Confirm password: ")
    if not password or password != confirmation:
        raise ValueError("A matching, non-empty password is required.")
    return password.encode("utf-8")


def _create_certificate(
    *,
    common_name: str,
    public_key,
    issuer_certificate: x509.Certificate | None,
    issuer_key,
    is_ca: bool,
    extended_usage: x509.ObjectIdentifier | None = None,
    server_names: list[str] | None = None,
) -> x509.Certificate:
    now = datetime.now(timezone.utc)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    issuer = issuer_certificate.subject if issuer_certificate else subject

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=is_ca, path_length=0 if is_ca else None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=is_ca,
                crl_sign=is_ca,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(public_key),
            critical=False,
        )
    )

    if issuer_certificate:
        builder = builder.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(
                issuer_certificate.public_key()
            ),
            critical=False,
        )

    if extended_usage:
        builder = builder.add_extension(
            x509.ExtendedKeyUsage([extended_usage]),
            critical=False,
        )

    if server_names is not None:
        names: list[x509.GeneralName] = [x509.DNSName("localhost")]
        names.append(x509.IPAddress(ipaddress.ip_address("127.0.0.1")))
        for server_name in server_names:
            try:
                name = x509.IPAddress(ipaddress.ip_address(server_name))
            except ValueError:
                name = x509.DNSName(server_name)
            if name not in names:
                names.append(name)
        builder = builder.add_extension(
            x509.SubjectAlternativeName(names),
            critical=False,
        )

    return builder.sign(
        private_key=issuer_key,
        algorithm=hashes.SHA256(),
    )


def _write_identity(
    output_dir: Path,
    name: str,
    private_key,
    certificate: x509.Certificate,
) -> None:
    _write_private_key(output_dir / f"{name}.key.pem", private_key)
    _write_certificate(output_dir / f"{name}.crt.pem", certificate)


def _write_private_key(
    path: Path,
    private_key,
    password: bytes | None = None,
) -> None:
    encryption = (
        serialization.BestAvailableEncryption(password)
        if password
        else serialization.NoEncryption()
    )
    path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption,
        )
    )


def _write_certificate(path: Path, certificate: x509.Certificate) -> None:
    path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))


def _write_pkcs12(
    path: Path,
    name: str,
    private_key,
    certificate: x509.Certificate,
    ca_certificate: x509.Certificate,
    password: bytes,
) -> None:
    data = pkcs12.serialize_key_and_certificates(
        name=name.encode("utf-8"),
        key=private_key,
        cert=certificate,
        cas=[ca_certificate],
        encryption_algorithm=serialization.BestAvailableEncryption(password),
    )
    path.write_bytes(data)


if __name__ == "__main__":
    main()
