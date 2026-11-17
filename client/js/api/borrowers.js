import { request } from "./http.js";

function toBorrower(dto) {
    return {
        id: dto.id,
        name: dto.name,
        email: dto.email,
    };
}

const toBorrowers = (list) => list.map(toBorrower);

export async function getAllBorrowers() {
    return toBorrowers(await request("/borrowers"));
}

export async function searchBorrowers(type, value) {
    const encodedValue = encodeURIComponent(value);
    switch (type) {
        case "borrower-id":
            return [toBorrower(await request(`/borrowers/${encodedValue}`))];
        case "borrower-name":
            return toBorrowers(await request(`/borrowers/search?text=${encodedValue}`));
        default:
            throw new Error(`Unknown search type for borrowers: ${type}`);
    }
}

export async function createBorrower({ name, email }) {
    const dto = await request("/borrowers", {
        method: "POST",
        body: { name, email },
    });
    return toBorrower(dto);
}

export async function deleteBorrower(borrowerId) {
    await request(`/borrowers/${encodeURIComponent(borrowerId)}`, { method: "DELETE" });
}