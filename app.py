import sqlite3, re, os
from datetime import date
from flask import Flask, request, jsonify, g, send_from_directory

DB = os.environ.get("LIB_DB", os.path.join(os.path.dirname(__file__), "library.db"))
app = Flask(__name__, static_folder="static")

SCHEMA = """
CREATE TABLE IF NOT EXISTS books(
  id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author TEXT NOT NULL,
  isbn TEXT NOT NULL UNIQUE, category TEXT NOT NULL DEFAULT 'General',
  available INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS members(
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS issues(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  member_id INTEGER NOT NULL REFERENCES members(id),
  issue_date TEXT NOT NULL, return_date TEXT);
"""

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close(_):
    d = g.pop("db", None)
    if d: d.close()

def init_db():
    c = sqlite3.connect(DB); c.executescript(SCHEMA); c.commit(); c.close()

def err(msg, code=400):
    return jsonify(error=msg), code

def body():
    return request.get_json(silent=True) or {}

BOOK_SQL = """SELECT b.*, m.name AS issued_to FROM books b
  LEFT JOIN issues i ON i.book_id=b.id AND i.return_date IS NULL
  LEFT JOIN members m ON m.id=i.member_id"""

@app.get("/")
def index():
    return send_from_directory("static", "index.html")

@app.get("/api/books")
def list_books():
    q = f"%{request.args.get('q', '').strip()}%"
    rows = db().execute(BOOK_SQL + " WHERE b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ? ORDER BY b.id DESC", (q, q, q)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/books")
def add_book():
    d = body()
    title, author = str(d.get("title", "")).strip(), str(d.get("author", "")).strip()
    isbn = re.sub(r"[\s-]", "", str(d.get("isbn", "")))
    cat = str(d.get("category", "")).strip() or "General"
    if not title or not author: return err("Title and author are required.")
    if not re.fullmatch(r"\d{9}[\dXx]|\d{13}", isbn): return err("ISBN must be 10 or 13 digits.")
    try:
        cur = db().execute("INSERT INTO books(title,author,isbn,category) VALUES(?,?,?,?)", (title, author, isbn, cat))
        db().commit()
    except sqlite3.IntegrityError:
        return err("A book with this ISBN already exists.", 409)
    return jsonify(id=cur.lastrowid), 201

@app.delete("/api/books/<int:bid>")
def delete_book(bid):
    b = db().execute("SELECT available FROM books WHERE id=?", (bid,)).fetchone()
    if not b: return err("Book not found.", 404)
    if not b["available"]: return err("Cannot delete a book that is currently issued.", 409)
    db().execute("DELETE FROM books WHERE id=?", (bid,)); db().commit()
    return jsonify(ok=True)

@app.get("/api/members")
def list_members():
    return jsonify([dict(r) for r in db().execute("SELECT * FROM members ORDER BY name")])

@app.post("/api/members")
def add_member():
    d = body()
    name, email = str(d.get("name", "")).strip(), str(d.get("email", "")).strip().lower()
    if not name: return err("Name is required.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email): return err("Valid email is required.")
    try:
        cur = db().execute("INSERT INTO members(name,email) VALUES(?,?)", (name, email)); db().commit()
    except sqlite3.IntegrityError:
        return err("A member with this email already exists.", 409)
    return jsonify(id=cur.lastrowid), 201

@app.post("/api/books/<int:bid>/issue")
def issue(bid):
    mid = body().get("member_id")
    b = db().execute("SELECT * FROM books WHERE id=?", (bid,)).fetchone()
    if not b: return err("Book not found.", 404)
    if not isinstance(mid, int) or not db().execute("SELECT 1 FROM members WHERE id=?", (mid,)).fetchone():
        return err("Valid member is required.", 400)
    if not b["available"]: return err("Book is already issued.", 409)
    db().execute("INSERT INTO issues(book_id,member_id,issue_date) VALUES(?,?,?)", (bid, mid, date.today().isoformat()))
    db().execute("UPDATE books SET available=0 WHERE id=?", (bid,)); db().commit()
    return jsonify(ok=True)

@app.post("/api/books/<int:bid>/return")
def return_book(bid):
    b = db().execute("SELECT * FROM books WHERE id=?", (bid,)).fetchone()
    if not b: return err("Book not found.", 404)
    if b["available"]: return err("This book is not currently issued.", 409)
    db().execute("UPDATE issues SET return_date=? WHERE book_id=? AND return_date IS NULL", (date.today().isoformat(), bid))
    db().execute("UPDATE books SET available=1 WHERE id=?", (bid,)); db().commit()
    return jsonify(ok=True)

@app.get("/api/issues")
def history():
    rows = db().execute("""SELECT i.*, b.title, m.name FROM issues i JOIN books b ON b.id=i.book_id
      JOIN members m ON m.id=i.member_id ORDER BY i.id DESC LIMIT 50""").fetchall()
    return jsonify([dict(r) for r in rows])

init_db()
if __name__ == "__main__":
    app.run(debug=True, port=5000)
