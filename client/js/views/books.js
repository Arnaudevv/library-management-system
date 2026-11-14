import * as booksApi from "../api/books.js";

// The 4 query buttons share the same try/catch and the same render
async function runQuery(queryFn) {
    try {
        renderBooks(await queryFn());
    } catch (error) {
        renderError(error.message);   // ApiError.message comes from the server
    }
}

function manageGetAllBooks() {
    runQuery(() => booksApi.getAllBooks());
}

function manageGetAvailableBooks() {
    runQuery(() => booksApi.getAvailableBooks());
}

function manageSearchBook() {
    const type  = document.getElementById("search-parameter").value;
    const value = document.getElementById("search-input").value.trim();
    if (!value) {
        console.log("Enter a value to search.")
        return
    }
    runQuery(() => booksApi.searchBooks(type, value));
}

function manageFilterByAuthor() {
    const authorId = document.getElementById("author-filter").value;
    runQuery(() => authorId ? booksApi.getBooksByAuthor(authorId) : booksApi.getAllBooks());
}

async function manageCreateBook(event) {
    event.preventDefault();
    const data = getCreateBookData();       // reads the form fields
    // validate here (empty title, no author, no ISBN...) before calling the API
    try {
        await booksApi.createBook(data);
        resetCreateBookForm();
        // refresh the list or show a success message
    } catch (error) {
        renderError(error.message);
    }
}