import * as authorsApi from "../api/authors.js";
import { renderAuthorOptions } from "./books.js";
import * as booksApi from "../api/books.js";

let selectedAuthorId = null;

// --------------------- QUERY MANAGER ----------------------
// The 4 query buttons share the same try/catch and the same render
async function runQuery(queryFn) {
    try {
        renderAuthors(await queryFn());
    } catch (error) {
        renderError(error.message);   
    }
}

function manageGetAllAuthors() {
    return runQuery(() => authorsApi.getAllAuthors());
}

function manageSearchAuthor() {
    const type  = document.getElementById("search-author-parameter").value;
    const value = document.getElementById("search-author-input").value.trim();
    if (!value) {
        renderError("Search input is empty.");   
        return
    }
    runQuery(() => authorsApi.searchAuthors(type, value));
}

async function manageCreateAuthor() {
    try {
        await authorsApi.createAuthor(getCreateAuthorData());
        await manageGetAllAuthors();
        await renderAuthorOptions();
        resetCreateAuthorForm();
    } catch (error) {
        renderError(error.message);   
    }
}

async function manageGetAuthorBooks(authorId, authorName) {
    selectedAuthorId = authorId;
    document.querySelector(".author-books-list").textContent = `${authorName}'s books`;

    try {
        const books = await authorsApi.getAuthorBooks(authorId);
        if (selectedAuthorId !== authorId) return;
        renderAuthorBooks(books);
    } catch (error) {
        console.error("Failed to load author's books:", error);
    }
}

manageGetAllAuthors()
/* ----------------------------------------------------------------------------------- */




/* ------------------------------------ VIEW ACTIONS & DOM ------------------------------------ */

// ----- GET ALL AUTHORS
document.getElementById('get-all-authors-btn').addEventListener('click', () => {
    manageGetAllAuthors()
    resetSearchAuthorByParametersValues()
})

// ----- SEARCH AUTHOR BY PARAMETERS
document.getElementById('search-author-by-paremeters-btn').addEventListener('click', manageSearchAuthor)

// ----- CREATE AUTHOR
document.getElementById('create-author-btn').addEventListener('click', () => {
    manageCreateAuthor()
})

// ----- DELETE AUTHOR
document.querySelector(".authors-list-container").addEventListener("click", async (event) => {
        const button = event.target.closest(".delete-author-btn");
        if (!button) return;

        const authorItem = button.closest(".author-item");
        const authorIdValue = authorItem?.dataset.authorId;
        const authorId = Number(authorIdValue);

        try {
            await authorsApi.deleteAuthor(authorId);
            authorItem.remove();
            if (authorId === selectedAuthorId) {
                selectedAuthorId = null;
                document.querySelector(".author-books-list").textContent = "Author's books";
                document.querySelector(".author-books-list-container").replaceChildren();
            }
            await renderAuthorOptions()
        } catch (error) {
            console.error("Failed to delete author:", error);
        }
    });

// ----- GET AUTHOR BOOKS
document.querySelector(".authors-list-container").addEventListener("click", (event) => {
        const button = event.target.closest(".get-author-books-btn");
        if (!button) return;

        const authorItem = button.closest(".author-item");
        const authorId = Number(authorItem?.dataset.authorId);
        const authorName = authorItem?.querySelector(".author-name")?.textContent.trim();

        if (!Number.isInteger(authorId) || authorId <= 0 || !authorName) {
            console.error("Cannot load books: invalid author ID.");
            return;
        }

        manageGetAuthorBooks(authorId, authorName);
    });

    
// -------------------- Helper Functions
function renderAuthors(authors) {
    const list = document.querySelector(".authors-list-container");

    list.innerHTML = authors.map((author) => `
        <item class="author-item" data-author-id="${author.id}">
            <h3 class="author-name">${author.name}</h3>
            <p class="author-nationality">${author.nationality}</p>
            <div class="author-actions">
                <button type="button" class="get-author-books-btn">📖</button>
                <button type="button" class="delete-author-btn">🗑️</button>
            </div>
        </item>`).join("");
}

function renderAuthorBooks(books) {
    const container = document.querySelector(".author-books-list-container");
    container.replaceChildren();

    if (books.length === 0) {
        const emptyMessage = document.createElement("p");
        emptyMessage.className = "author-books-empty";
        emptyMessage.textContent = "This author has no books.";
        container.append(emptyMessage);
        return;
    }

    for (const book of books) {
        const item = document.createElement("div");
        item.className = "author-book-item";

        const title = document.createElement("h4");
        title.textContent = book.title;

        const details = document.createElement("p");
        details.textContent =
            `ISBN: ${book.isbn ?? "-"} · Year: ${book.year ?? "-"}`;

        item.append(title, details);
        container.append(item);
    }
}

function getCreateAuthorData() {
    const name = document.getElementById("create-author-name-input").value.trim();
    const nationality = document.getElementById("create-author-nationality").value;
    return { name, nationality };
}


function resetSearchAuthorByParametersValues() {
    document.getElementById("search-author-parameter").value = "author-id";
    document.getElementById("search-author-input").value = "";
}

function resetCreateAuthorForm() {
    document.getElementById("create-author-form").reset();
}

