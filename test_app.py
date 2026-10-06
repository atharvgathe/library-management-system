import os, tempfile, unittest
os.environ["LIB_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
import app as a

class T(unittest.TestCase):
    def setUp(self):
        a.init_db(); self.c = a.app.test_client()
    def tearDown(self):
        import sqlite3; x = sqlite3.connect(a.DB); x.executescript("DELETE FROM issues;DELETE FROM books;DELETE FROM members;"); x.commit(); x.close()
    def book(self, isbn="9780140449136"):
        return self.c.post("/api/books", json={"title": "Odyssey", "author": "Homer", "isbn": isbn, "category": "Epic"})
    def member(self):
        return self.c.post("/api/members", json={"name": "Ana", "email": "ana@x.com"}).get_json()["id"]
    def test_add_list_search(self):
        self.assertEqual(self.book().status_code, 201)
        self.assertEqual(len(self.c.get("/api/books?q=homer").get_json()), 1)
        self.assertEqual(self.c.get("/api/books?q=zzz").get_json(), [])
    def test_validation_and_duplicates(self):
        self.assertEqual(self.c.post("/api/books", json={"title": "", "author": "x", "isbn": "1"}).status_code, 400)
        self.assertEqual(self.c.post("/api/books", json={"title": "a", "author": "b", "isbn": "abc"}).status_code, 400)
        self.book(); self.assertEqual(self.book().status_code, 409)
        self.assertEqual(self.c.post("/api/members", json={"name": "A", "email": "bad"}).status_code, 400)
    def test_issue_return_flow(self):
        bid = self.book().get_json()["id"]; mid = self.member()
        self.assertEqual(self.c.post(f"/api/books/{bid}/return").status_code, 409)   # not issued
        self.assertEqual(self.c.post(f"/api/books/{bid}/issue", json={"member_id": mid}).status_code, 200)
        self.assertEqual(self.c.post(f"/api/books/{bid}/issue", json={"member_id": mid}).status_code, 409)  # already issued
        self.assertEqual(self.c.delete(f"/api/books/{bid}").status_code, 409)         # issued can't be deleted
        self.assertEqual(self.c.post(f"/api/books/{bid}/return").status_code, 200)
        self.assertEqual(self.c.get("/api/issues").get_json()[0]["return_date"] is not None, True)
        self.assertEqual(self.c.delete(f"/api/books/{bid}").status_code, 200)
    def test_missing(self):
        self.assertEqual(self.c.delete("/api/books/999").status_code, 404)
        self.assertEqual(self.c.post("/api/books/999/issue", json={"member_id": 1}).status_code, 404)
        bid = self.book().get_json()["id"]
        self.assertEqual(self.c.post(f"/api/books/{bid}/issue", json={"member_id": 99}).status_code, 400)
    def test_index(self):
        self.assertEqual(self.c.get("/").status_code, 200)

if __name__ == "__main__": unittest.main()

class AssetTests(unittest.TestCase):
    def test_page_assets_load(self):
        import re
        c = a.app.test_client()
        html = c.get("/").get_data(as_text=True)
        refs = re.findall(r'(?:href|src)="(/static/[^"]+)"', html)
        assert len(refs) == 2, refs
        for r in refs:
            self.assertEqual(c.get(r).status_code, 200, r)
