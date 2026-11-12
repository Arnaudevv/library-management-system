# API Requests

## Authors

POST /authors HTTP/1.1
GET /authors HTTP/1.1
GET /authors/{author_id} HTTP/1.1
GET /authors?name={name} HTTP/1.1
GET /authors/search?text={text} HTTP/1.1
GET /authors/{author_id}/books HTTP/1.1
DELETE /authors/{author_id} HTTP/1.1

## Books

POST /books HTTP/1.1
GET /books HTTP/1.1
GET /books/{book_id} HTTP/1.1
GET /books?isbn={isbn} HTTP/1.1
GET /books/search?text={text} HTTP/1.1
GET /authors/{author_id}/books HTTP/1.1
GET /books/with-authors HTTP/1.1
GET /books/{book_id}/loans HTTP/1.1
GET /books/available HTTP/1.1
DELETE /books/{book_id} HTTP/1.1

## Borrowers

POST /borrowers HTTP/1.1
GET /borrowers HTTP/1.1
GET /borrowers/{borrower_id} HTTP/1.1
GET /borrowers?email={email} HTTP/1.1
GET /borrowers/search?text={text} HTTP/1.1
GET /borrowers/{borrower_id}/loans HTTP/1.1
DELETE /borrowers/{borrower_id} HTTP/1.1

## Loans

POST /loans HTTP/1.1
GET /loans HTTP/1.1
GET /loans/{loan_id} HTTP/1.1
GET /books/{book_id}/loans HTTP/1.1
GET /borrowers/{borrower_id}/loans HTTP/1.1
GET /loans/active HTTP/1.1
GET /loans/history HTTP/1.1
GET /loans/with-relations HTTP/1.1
GET /loans/{loan_id}/relations HTTP/1.1
DELETE /loans/{loan_id} HTTP/1.1
