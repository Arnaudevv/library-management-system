const BASE_URL = "";
const DIGEST_HEADER = "X-Content-Digest";

export class ApiError extends Error {
    constructor(code, message, status) {
        super(message);
        this.code = code;
        this.status = status;
    }
}

export async function request(path, { method = "GET", body } = {}) {
    const bodyText = body === undefined ? "" : JSON.stringify(body);
    const bodyBytes = new TextEncoder().encode(bodyText);
    const headers = {
        [DIGEST_HEADER]: await sha256Hex(bodyBytes),
    };
    if (body !== undefined) {
        headers["Content-Type"] = "application/json";
    }

    let response;
    try {
        response = await fetch(BASE_URL + path, {
            method,
            headers,
            body: body === undefined ? undefined : bodyText,
        });
    } catch {
        throw new ApiError(
            "network_error",
            "Could not reach the server. Check HTTPS and your client certificate.",
            0,
        );
    }

    const responseBytes = new Uint8Array(await response.arrayBuffer());
    const receivedDigest = response.headers.get(DIGEST_HEADER);
    const expectedDigest = await sha256Hex(responseBytes);
    if (
        receivedDigest === null
        || receivedDigest.trim().toLowerCase() !== expectedDigest
    ) {
        throw new ApiError(
            "integrity_error",
            "Response integrity verification failed.",
            response.status,
        );
    }

    let data = null;
    if (responseBytes.length > 0) {
        try {
            data = JSON.parse(new TextDecoder().decode(responseBytes));
        } catch {
            throw new ApiError(
                "invalid_response",
                "The server returned an invalid JSON response.",
                response.status,
            );
        }
    }

    if (!response.ok) {
        const { code, message } = data?.error ?? {};
        throw new ApiError(code ?? "unknown_error", message ?? "Unexpected error.", response.status);
    }
    return data;
}

async function sha256Hex(bytes) {
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (byte) =>
        byte.toString(16).padStart(2, "0")
    ).join("");
}