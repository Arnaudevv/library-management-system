import { request } from "./http.js";

function toLoan(dto) {
    return {
        id: dto.id,
        bookId: dto.book_id,
        borrowerId: dto.borrower_id,
        loanDate: dto.loan_date,
        dueDate: dto.due_date,
        returnDate: dto.return_date,
        bookTitle: dto.book_title,
        borrowerName: dto.borrower_name,
    };
}

const toLoans = (list) => list.map(toLoan);

export async function getAllLoans() {
    return toLoans(await request("/loans"));
}

export async function getActiveLoans() {
    return toLoans(await request("/loans/active"));
}

export async function getReturnedLoans() {
    return toLoans(await request("/loans/history"));
}

export async function getBorrowerLoans(borrowerId) {
    const encodedId = encodeURIComponent(borrowerId);
    return toLoans(await request(`/loans/by-borrower/${encodedId}`));
}

export async function createLoan({ bookId, borrowerId, dueDate }) {
    const dto = await request("/loans", {
        method: "POST",
        body: {
            book_id: bookId,
            borrower_id: borrowerId,
            due_date: dueDate,
        },
    });
    return toLoan(dto);
}

export async function returnLoan(loanId) {
    const encodedId = encodeURIComponent(loanId);
    return toLoan(await request(`/loans/${encodedId}/return`, { method: "POST" }));
}
