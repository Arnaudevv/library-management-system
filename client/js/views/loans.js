import * as borrowersApi from "../api/borrowers.js";
import * as booksApi from "../api/books.js";
import * as loansApi from "../api/loans.js";

let currentFilter = "all";

async function loadLoans() {
    const loaders = {
        all: loansApi.getAllLoans,
        active: loansApi.getActiveLoans,
        returned: loansApi.getReturnedLoans,
    };

    try {
        renderLoans(await loaders[currentFilter]());
    } catch (error) {
        console.error("Failed to load loans:", error);
    }
}

async function loadLoanOptions() {
    try {
        const [books, borrowers] = await Promise.all([
            booksApi.getAvailableBooks(),
            borrowersApi.getAllBorrowers(),
        ]);
        renderBookOptions(books);
        renderBorrowerOptions(borrowers);
    } catch (error) {
        console.error("Failed to load loan form options:", error);
    }
}

function renderLoans(loans) {
    const list = document.querySelector(".loans-list-container");
    const items = loans.map((loan) => {
        const item = document.createElement("article");
        item.className = "loan-item";
        item.dataset.loanId = loan.id;
        item.dataset.bookId = loan.bookId;
        item.dataset.borrowerId = loan.borrowerId;

        const details = document.createElement("div");
        details.className = "loan-details";

        const title = document.createElement("h3");
        title.className = "loan-book-title";
        title.textContent = loan.bookTitle ?? "Unknown book";

        const borrower = document.createElement("p");
        borrower.className = "loan-borrower-name";
        borrower.textContent = `Borrower: ${loan.borrowerName ?? "Unknown borrower"}`;

        const dates = document.createElement("p");
        dates.className = "loan-dates";
        dates.textContent = [
            `Start: ${loan.loanDate ?? "-"}`,
            `Due: ${loan.dueDate ?? "-"}`,
            loan.returnDate ? `Returned: ${loan.returnDate}` : null,
        ].filter(Boolean).join(" · ");

        details.append(title, borrower, dates);
        item.append(details);

        if (!loan.returnDate) {
            const returnButton = document.createElement("button");
            returnButton.type = "button";
            returnButton.className = "return-loan-btn";
            returnButton.textContent = "Return book";
            item.append(returnButton);
        }

        return item;
    });

    list.replaceChildren(...items);
}

function renderBookOptions(books) {
    const select = document.getElementById("loan-book-select");
    const placeholder = new Option(
        books.length ? "Select a book" : "No available books",
        "",
        true,
        true,
    );
    placeholder.disabled = true;
    select.replaceChildren(
        placeholder,
        ...books.map((book) => new Option(book.title, book.id)),
    );
}

function renderBorrowerOptions(borrowers) {
    const select = document.getElementById("loan-borrower-select");
    const placeholder = new Option(
        borrowers.length ? "Select a borrower" : "No borrowers available",
        "",
        true,
        true,
    );
    placeholder.disabled = true;
    select.replaceChildren(
        placeholder,
        ...borrowers.map((borrower) => new Option(borrower.name, borrower.id)),
    );
}

async function manageCreateLoan() {
    const form = document.getElementById("create-loan-form");
    if (!form.reportValidity()) return;

    const data = {
        bookId: Number(document.getElementById("loan-book-select").value),
        borrowerId: Number(document.getElementById("loan-borrower-select").value),
        dueDate: document.getElementById("loan-due-date").value,
    };

    try {
        await loansApi.createLoan(data);
        form.reset();
        await Promise.all([loadLoanOptions(), loadLoans()]);
    } catch (error) {
        console.error("Failed to create loan:", error);
    }
}

document.querySelector(".loan-filter-buttons").addEventListener("click", (event) => {
    const button = event.target.closest("[data-loan-filter]");
    if (!button) return;

    currentFilter = button.dataset.loanFilter;
    document.querySelectorAll(".loan-filter-btn").forEach((filterButton) => {
        filterButton.classList.toggle("active", filterButton === button);
    });
    loadLoans();
});

document.getElementById("create-loan-btn")
    .addEventListener("click", manageCreateLoan);

document.querySelector(".loans-list-container").addEventListener("click", async (event) => {
    const button = event.target.closest(".return-loan-btn");
    if (!button) return;

    const loanItem = button.closest(".loan-item");
    const loanId = Number(loanItem?.dataset.loanId);
    if (!Number.isInteger(loanId) || loanId <= 0) {
        console.error("Cannot return book: invalid loan ID.");
        return;
    }

    button.disabled = true;
    try {
        await loansApi.returnLoan(loanId);
        await Promise.all([loadLoans(), loadLoanOptions()]);
    } catch (error) {
        console.error("Failed to return book:", error);
        button.disabled = false;
    }
});

loadLoans();
loadLoanOptions();
