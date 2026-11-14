import * as booksApi from "../api/books.js";

/* ------------------------------------ API USAGE ------------------------------------ */

// The 4 query buttons share the same try/catch and the same render
async function runQuery(queryFn) {
    try {
        renderBooks(await queryFn());
    } catch (error) {
        console.log("errror detected" + error.message)
        // renderError(error.message);   
        // ApiError.message comes from the server
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
    const data = getCreateBookData();       
    try {
        await booksApi.createBook(data);
        resetCreateBookForm();
    } catch (error) {
        renderError(error.message);
    }
}

/* ----------------------------------------------------------------------------------- */




/* ------------------------------------ VIEW ACTIONS & DOM ------------------------------------ */
function renderBooks(books) {
    const list = document.querySelector(".books-list-container");

    list.innerHTML = books.map((book) => `
        <item class="book-item" data-book-id="${book.id}">
            <h3 class="book-title">${book.title}</h3>
            <span class="book-author">${book.authorName}</span>
            <span class="book-isbn">${book.isbn ?? "-"}</span>
            <span class="book-year">${book.year ?? "-"}</span>
            <button type="button" class="delete-book-btn">🗑️</button>
        </item>`).join("");
}



// ----- GET ALL BOOKS
document.getElementById('get-all-books-btn').addEventListener('click', () => {
    manageGetAllBooks()
    resetBookSearchFilters()
})

// ----- GET ALL AVAILABLE BOOKS
document.getElementById('get-all-available-books-btn').addEventListener('click', () => {
    manageGetAvailableBooks()
    resetBookSearchFilters()
})

// ----- GET ALL AVAILABLE BOOKS
document.getElementById('search-book-by-paremeters-btn').addEventListener('click', () => {
    console.log("asdas")
    manageSearchBook()
    resetBookSearchFilters()
})

// ----- CREATE BOOK
document.getElementById('create-book-btn').addEventListener('submit', manageCreateBook)

// ----- DELETE BOOK
document.querySelector(".books-list-container").addEventListener("click", async (event) => {
    const button = event.target.closest(".delete-book-btn");
    if (!button) return;

    const bookItem = button.closest(".book-item");
    const bookIdValue = bookItem?.dataset.bookId;
    const bookId = Number(bookIdValue);
    if (!bookIdValue || !Number.isInteger(bookId) || bookId <= 0) {
        console.error("Cannot delete book: the item has no valid book ID.");
        return;
    }

    try {
        await booksApi.deleteBook(bookId);
        bookItem.remove();
    } catch (error) {
        console.error("Failed to delete book:", error);
    }
});





// ----- Helper Functions

function getCreateBookData() {
    const title = document
        .getElementById("create-book-title-input")
        .value
        .trim();

    const authorValue = document.getElementById("create-book-author").value;
    const isbnText = document
        .getElementById("create-book-isbn")
        .textContent
        .trim();
    const yearValue = document.getElementById("create-book-year").value;

    return {
        title,
        authorId: authorValue === "" ? null : Number(authorValue),
        isbn: !isbnText || isbnText === "Not generated" ? null : isbnText,
        year: yearValue === "" ? null : Number(yearValue),
    };
}

function resetCreateBookForm() {
    document.getElementById("create-book-form").reset();
    document.getElementById("create-book-isbn").textContent = "Not generated";
}

function resetBookSearchFilters() {
    document.getElementById("search-parameter").value = "book-id";
    document.getElementById("search-input").value = "";
    document.getElementById("author-filter").value = "";
}
