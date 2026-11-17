import * as booksApi from "../api/books.js";
import * as authorsApi from "../api/authors.js"

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
    const type  = document.getElementById("search-book-parameter").value;
    const value = document.getElementById("search-book-input").value.trim();
    if (!value) {
        renderError("Search input is empty.");   
        return
    }
    runQuery(() => booksApi.searchBooks(type, value));
}

function manageFilterByAuthor() {
    const authorId = document.getElementById("book-by-author-filter").value;
    runQuery(() => authorId ? booksApi.getBooksByAuthor(authorId) : booksApi.getAllBooks());
}

async function manageCreateBook() {
    const data = getCreateBookData();       
    try {
        await booksApi.createBook(data);
        await manageGetAllBooks();
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
    resetSearchBookByParameters()
    resetSearchBookByAuthors()
})

// ----- GET ALL AVAILABLE BOOKS
document.getElementById('get-all-available-books-btn').addEventListener('click', () => {
    manageGetAvailableBooks()
    resetSearchBookByParameters()
    resetSearchBookByAuthors()
})

// ----- SEARCH BOOK BY PARAMETERS
document.getElementById('search-book-by-paremeters-btn').addEventListener('click', () => {
    console.log("asdas")
    manageSearchBook()
    resetSearchBookByAuthors()
})

// ------ GET BOOKS BY AUTHOR
document.getElementById('author-filter-btn').addEventListener('click', () => {
    manageFilterByAuthor()
    resetSearchBookByParameters()
})

// ----- CREATE BOOK
document.getElementById('create-book-btn').addEventListener('click', () => {
    manageCreateBook()
})

// ----- DELETE BOOK
document.querySelector(".books-list-container").addEventListener("click", async (event) => {
    const button = event.target.closest(".delete-book-btn");
    if (!button) return;

    const bookItem = button.closest(".book-item");
    const bookIdValue = bookItem?.dataset.bookId;
    const bookId = Number(bookIdValue);

    try {
        await booksApi.deleteBook(bookId);
        bookItem.remove();
    } catch (error) {
        console.error("Failed to delete book:", error);
    }
});




manageGetAllBooks()
renderAuthorOptions()


// -------------------- Helper Functions

function getCreateBookData() {
    const title = document.getElementById("create-book-title-input").value.trim();

    const authorValue = document.getElementById("create-book-author").value;
    const isbnText = document.getElementById("create-book-isbn").textContent.trim();
    const yearValue = document.getElementById("create-book-year").value;

    return {
        title,
        authorId: authorValue === "" ? null : Number(authorValue),
        isbn: !isbnText || isbnText === "Not generated" ? null : isbnText,
        year: yearValue === "" ? null : Number(yearValue),
    };
}

function resetCreateBookForm() {
    document.getElementById("create-book-title-input").value = "";
    document.getElementById("create-book-author").value = "";
    document.getElementById("create-book-year").value = "";

    const isbn = document.getElementById("create-book-isbn");
    isbn.textContent = "Not generated";
    isbn.classList.remove("generated");
}

function resetSearchBookByParameters() {
    document.getElementById("search-book-parameter").value = "book-id";
    document.getElementById("search-book-input").value = "";
}

function resetSearchBookByAuthors() {
    document.getElementById("book-by-author-filter").value = "";
}


// --- Generate random ISBN
const generateButton = document.getElementById("generate-isbn-btn");
const isbnField = document.getElementById("create-book-isbn");

generateButton.addEventListener("click", () => {
    const base = "978" + Array.from({ length: 9 }, () =>
        Math.floor(Math.random() * 10)
    ).join("");

    const sum = [...base].reduce(
        (total, digit, index) => total + Number(digit) * (index % 2 === 0 ? 1 : 3),
        0
    );

    const checkDigit = (10 - (sum % 10)) % 10;

    isbnField.textContent = base + checkDigit;
    isbnField.classList.add("generated");
});


// --- UPDATE AUTHORS LIST ON AUTHOR ACTIONS
export async function renderAuthorOptions() {
    let authors;
    try {
        authors = await authorsApi.getAllAuthors();
    } catch (error) {
        renderError(error.message);
        return;
    }

    const selects = [
        document.getElementById("book-by-author-filter"),
        document.getElementById("create-book-author"),
    ];

    selects.forEach(select => {
        const previous = select.value;
        const placeholder = select.options[0];

        select.replaceChildren(
            placeholder,
            ...authors.map(author => new Option(author.name, author.id))
        );

        select.value = previous;
        if (select.selectedIndex === -1) select.value = "";
    });
}