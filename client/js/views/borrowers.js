import * as borrowersApi from "../api/borrowers.js";
import * as loansApi from "../api/loans.js";

// --------------------- QUERY MANAGER ----------------------
// The 4 query buttons share the same try/catch and the same render
let selectedBorrowerId = null;

async function runQuery(queryFn) {
    try {
        renderBorrowers(await queryFn());
    } catch (error) {
        console.error("Failed to load borrowers:", error);
    }
}

function manageGetAllBorrowers() {
    return runQuery(() => borrowersApi.getAllBorrowers());
}

function manageSearchBorrower() {
    const type = document.getElementById("search-borrower-parameter").value;
    const value = document.getElementById("search-borrower-input").value.trim();
    if (!value) {
        console.error("Search input is empty.");
        return;
    }
    return runQuery(() => borrowersApi.searchBorrowers(type, value));
}

async function manageCreateBorrower() {
    try {
        await borrowersApi.createBorrower(getCreateBorrowerData());
        await manageGetAllBorrowers();
        resetCreateBorrowerForm();
    } catch (error) {
        console.error("Failed to create borrower:", error);
    }
}

async function manageGetBorrowerLoans(borrowerId, borrowerName) {
    selectedBorrowerId = borrowerId;
    document.querySelector(".borrower-loans-list").textContent = `${borrowerName}'s loans`;
    document.querySelector(".borrower-loans-list-container").replaceChildren();

    try {
        const loans = await loansApi.getBorrowerLoans(borrowerId);
        if (selectedBorrowerId !== borrowerId) return;
        renderBorrowerLoans(loans);
    } catch (error) {
        console.error("Failed to load borrower's loans:", error);
    }
}

manageGetAllBorrowers();
/* ----------------------------------------------------------------------------------- */

/* ------------------------------------ VIEW ACTIONS & DOM ------------------------------------ */

function renderBorrowers(borrowers) {
    const list = document.querySelector(".borrowers-list-container");
    const items = borrowers.map((borrower) => {
        const item = document.createElement("item");
        item.className = "borrower-item";
        item.dataset.borrowerId = borrower.id;

        const name = document.createElement("h3");
        name.className = "borrower-name";
        name.textContent = borrower.name;

        const email = document.createElement("p");
        email.className = "borrower-email";
        email.textContent = borrower.email;

        const actions = document.createElement("div");
        actions.className = "borrower-actions";

        const loansButton = document.createElement("button");
        loansButton.type = "button";
        loansButton.className = "get-borrower-loans-btn";
        loansButton.textContent = "🔖";
        loansButton.setAttribute("aria-label", `Show ${borrower.name}'s loans`);

        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "delete-borrower-btn";
        deleteButton.textContent = "🗑️";

        actions.append(loansButton, deleteButton);
        item.append(name, email, actions);
        return item;
    });

    list.replaceChildren(...items);
}

function renderBorrowerLoans(loans) {
    const container = document.querySelector(".borrower-loans-list-container");
    if (loans.length === 0) {
        const emptyMessage = document.createElement("p");
        emptyMessage.className = "borrower-loans-empty";
        emptyMessage.textContent = "This borrower has no loans.";
        container.replaceChildren(emptyMessage);
        return;
    }

    const items = loans.map((loan) => {
        const item = document.createElement("div");
        item.className = "borrower-loan-item";
        item.dataset.loanId = loan.id;
        item.dataset.bookId = loan.bookId;

        const title = document.createElement("h4");
        title.textContent = loan.bookTitle ?? "Unknown book";

        const details = document.createElement("p");
        details.textContent = [
            `Loan date: ${loan.loanDate ?? "-"}`,
            `Due date: ${loan.dueDate ?? "-"}`,
            `Return date: ${loan.returnDate ?? "Not returned"}`,
        ].join(" · ");

        item.append(title, details);
        return item;
    });

    container.replaceChildren(...items);
}

function getCreateBorrowerData() {
    return {
        name: document.getElementById("create-borrower-name-input").value.trim(),
        email: document.getElementById("create-borrower-email-input").value.trim(),
    };
}

function resetSearchBorrowerByParameters() {
    document.getElementById("search-borrower-parameter").value = "borrower-id";
    document.getElementById("search-borrower-input").value = "";
}

function resetCreateBorrowerForm() {
    document.getElementById("create-borrower-form").reset();
}

// ----- GET ALL BORROWERS
document.getElementById("get-all-borrowers-btn").addEventListener("click", () => {
    manageGetAllBorrowers();
    resetSearchBorrowerByParameters();
});

// ----- SEARCH BORROWERS BY PARAMETERS
document.getElementById("search-borrower-by-parameters-btn")
    .addEventListener("click", manageSearchBorrower);

// ----- CREATE BORROWER
document.getElementById("create-borrower-btn")
    .addEventListener("click", manageCreateBorrower);

// ----- DELETE BORROWER
document.querySelector(".borrowers-list-container").addEventListener("click", async (event) => {
    const loansButton = event.target.closest(".get-borrower-loans-btn");
    if (loansButton) {
        const borrowerItem = loansButton.closest(".borrower-item");
        const borrowerId = Number(borrowerItem?.dataset.borrowerId);
        const borrowerName = borrowerItem?.querySelector(".borrower-name")?.textContent.trim();
        if (!Number.isInteger(borrowerId) || borrowerId <= 0 || !borrowerName) {
            console.error("Cannot load loans: invalid borrower information.");
            return;
        }

        manageGetBorrowerLoans(borrowerId, borrowerName);
        return;
    }

    const button = event.target.closest(".delete-borrower-btn");
    if (!button) return;

    const borrowerItem = button.closest(".borrower-item");
    const borrowerId = Number(borrowerItem?.dataset.borrowerId);
    if (!Number.isInteger(borrowerId) || borrowerId <= 0) {
        console.error("Cannot delete borrower: invalid borrower ID.");
        return;
    }

    try {
        await borrowersApi.deleteBorrower(borrowerId);
        borrowerItem.remove();
        if (borrowerId === selectedBorrowerId) {
            selectedBorrowerId = null;
            document.querySelector(".borrower-loans-list").textContent = "Borrower's loans";
            document.querySelector(".borrower-loans-list-container").replaceChildren();
        }
    } catch (error) {
        console.error("Failed to delete borrower:", error);
    }
});
