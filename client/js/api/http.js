const BASE_URL = "http://127.0.0.1:8000";

export class ApiError extends Error {
    constructor(code, message, status) {
        super(message);
        this.code = code;
        this.status = status;
    }
}

export async function request(path, { method = "GET", body } = {}) {
    let response;
    try {
        response = await fetch(BASE_URL + path, {
            method,
            headers: body ? { "Content-Type": "application/json" } : {},
            body: body ? JSON.stringify(body) : undefined,
        });
    } catch {
        throw new ApiError("network_error", "Could not reach the server.", 0);
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
        const { code, message } = data?.error ?? {};
        throw new ApiError(code ?? "unknown_error", message ?? "Unexpected error.", response.status);
    }
    return data;
}