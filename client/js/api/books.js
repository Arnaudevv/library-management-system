import { request } from "./http.js";

function toBook(dto) {
    return {
        id: dto.id,
        title: dto.title,
        authorId: dto.author_id,
        isbn: dto.isbn,
        year: dto.publication_year,
    };
}

const toBooks = (list) => list.map(toBook);

export async function getAllBooks() {
    return toBooks(await request("/books"));
}

export async function getAvailableBooks() {
    return toBooks(await request("/books/available"));
}

export async function getBooksByAuthor(authorId) {
    return toBooks(await request(`/books/by-author/${authorId}`));
}

export async function searchBooks(type, value) {
    const v = encodeURIComponent(value);
    switch (type) {
        case "book-id":    return [toBook(await request(`/books/${v}`))];
        case "book-isbn":  return [toBook(await request(`/books?isbn=${v}`))];
        case "book-title": return toBooks(await request(`/books/search?text=${v}`));
        default: throw new Error(`Unknown search type: ${type}`);
    }
}

export async function createBook({ title, authorId, isbn, year }) {
    const dto = await request("/books", {
        method: "POST",
        body: { title, author_id: authorId, isbn, publication_year: year },
    });
    return toBook(dto);
}
