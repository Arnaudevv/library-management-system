import { request } from "./http.js";
import { toBooks } from "../api/books.js"

function toAuthor(dto) {
    return {
        id: dto.id,
        name: dto.name,
        nationality: dto.nationality,
    };
}

const toAuthors = (list) => list.map(toAuthor);

export async function getAllAuthors(params) {
    return toAuthors(await request("/authors"));
}

export async function searchAuthors(type, value) {
    const v = encodeURIComponent(value);
    switch (type) {
        case "author-id": return [toAuthor(await request(`/authors/${v}`))]
        case "author-name": return toAuthors(await request(`/authors/search?text=${v}`))
        default: throw new Error(`Unknown search type for authors: ${v}`)
    }
}

export async function createAuthor({ name, nationality }) {
    const dto = await request("/authors", {
        method: "POST",
        body: { name, nationality },
    });
    return toAuthor(dto);
}

export async function deleteAuthor(authorId) {
    await request(`/authors/${authorId}`, { method: "DELETE" });
}

export async function getAuthorBooks(authorId) {
    return toBooks(await request(`/books/by-author/${authorId}`));
}