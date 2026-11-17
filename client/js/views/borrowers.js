import * as borrowersApi from "../api/borrowers.js";

// --------------------- QUERY MANAGER ----------------------
// The 4 query buttons share the same try/catch and the same render
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
manageGetAllBorrowers()
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

        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "delete-borrower-btn";
        deleteButton.textContent = "🗑️";

        actions.append(deleteButton);
        item.append(name, email, actions);
        return item;
    });

    list.replaceChildren(...items);
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
    } catch (error) {
        console.error("Failed to delete borrower:", error);
    }
});
