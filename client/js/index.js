// ------------------ HEADER (View Switcher) ------------------
const VIEWS = {
    "books-btn": document.querySelector(".books-view"),
    "authors-btn": document.querySelector(".authors-view"),
    "borrowers-btn": document.querySelector(".borrowers-view"),
    "loans-btn": document.querySelector(".loans-view"),
};

function showView(buttonId) {
    for (const [id, view] of Object.entries(VIEWS)) {
        const isActive = id === buttonId;
        view.classList.toggle("active", isActive);
        document.getElementById(id).classList.toggle("active", isActive);
    }
}

for (const id of Object.keys(VIEWS)) {
    document.getElementById(id).addEventListener("click", () => showView(id));
}

showView("books-btn");   // initial view

// ------------------------------------------------------------