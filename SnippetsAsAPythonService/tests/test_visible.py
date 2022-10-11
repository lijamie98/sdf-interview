# required for CodeSignal unit tests: add current directory into search path
import os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, os.path.dirname(currentdir))

from helpers import *
import solution, runner

server = runner.ServerManager.create(solution.app)  # keep this!


class TestFunctionalityVisible(SnippetTestCase):
    def __init__(self, *a, **kw):
        super().__init__(server, *a, **kw)

    def test_creation_basics(self):
        r = post("snippets", json=make_request("recipe"))
        self.assertIsNotNone(r)
        return r

    def test_creation_status_code(self):
        r = self.test_creation_basics()
        self.assertIsNotNone(r)
        self.assertGreaterEqual(r.status_code, 200)
        self.assertLess(r.status_code, 300)

    def test_retrieval_basics(self):
        self.test_creation_basics()
        r = get("snippets/recipe")
        self.assertIsNotNone(r)
        return r

    def test_retrieval_schema_types(self):
        r = self.test_creation_basics()
        try:
            js = r.json()
            self.assertIsNotNone(js)
        except:
            self.fail("bad json: " + r.text)

        for field in ("name", "snippet", "url", "expires_at"):
            self.assertIn(field, js.keys())
            self.assertIsInstance(js[field], str)

    def test_retrieval_missing(self):
        r = get("missing")
        self.assertIsNotNone(r)
        self.assertEqual(404, r.status_code)

    def test_negative_expiration(self):
        r = post("snippets", json=make_request("test", exp=-2))
        self.assertIsNotNone(r)
        self.assertGreaterEqual(r.status_code, 400)
        self.assertLess(r.status_code, 500)


def make_request(name, exp=2):
    return {"name": name, "expires_in": exp, "snippet": "content"}
