# Library Management System

## Description
A full-stack web application for managing a library. Users can add, search, issue, return and delete books, and add members to whom books are issued. The page updates dynamically (no reloads) through the Fetch API, and all data is stored persistently in an SQLite database.

## Features
- Add a book (Title, Author, ISBN, Category) with validation (required fields, 10/13-digit ISBN, no duplicate ISBN)
- View all books and search by title, author or ISBN; filter by Available / Issued
- Issue a book to a member and return it; issue history is recorded
- A book that is already issued cannot be issued again; a book that is not issued cannot be returned
- Delete a book (blocked while it is issued)
- Add and list members (valid, unique email)
- Live dashboard: total, available and issued books, and member count

## Technologies / Tools Used
- **Frontend:** HTML, CSS, JavaScript (Fetch API)
- **Frontend tooling:** Node.js, npm, esbuild (minifies and bundles `src/` into `static/`)
- **Backend:** Python, Flask (REST API)
- **Database:** SQLite
- **Testing:** Python `unittest`

## Project Structure
    app.py            Flask REST API + serves the frontend
    src/              Frontend source (index.html, style.css, app.js)
    static/           Built frontend served by Flask (pre-built, included)
    build.js          Node.js build script (esbuild)
    dev.js            Node.js script: frontend watcher + Flask together
    test_app.py       Automated tests
    requirements.txt  Python dependencies
    package.json      Node scripts and dev dependency

## How to Run
**Prerequisites:** Python 3.9+ (Node.js 18+ is optional, only to rebuild the frontend)

1. Clone the repository and open the folder:
        git clone <your-repository-url>
        cd <repository-folder>
2. Install Python dependencies:
        pip install -r requirements.txt
3. Start the server:
        python app.py
4. Open **http://127.0.0.1:5000** in your browser. The `library.db` database is created automatically on first run.

**Optional: rebuild the frontend with Node.js**

    npm install
    npm start        # build frontend, then run Flask
    npm run dev      # rebuild on change + run Flask

## Run the Tests
    python -m unittest test_app.py -v

## REST API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/books?q= | List / search by title, author, ISBN |
| POST | /api/books | Add a book |
| DELETE | /api/books/&lt;id&gt; | Delete a book (blocked if issued) |
| GET | /api/members | List members |
| POST | /api/members | Add a member |
| POST | /api/books/&lt;id&gt;/issue | Issue a book `{member_id}` |
| POST | /api/books/&lt;id&gt;/return | Return a book |
| GET | /api/issues | Issue history |

## Database Schema
- **books**(id, title, author, isbn UNIQUE, category, available)
- **members**(id, name, email UNIQUE)
- **issues**(id, book_id -> books, member_id -> members, issue_date, return_date)
