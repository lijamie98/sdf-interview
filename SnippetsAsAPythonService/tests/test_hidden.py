# required for CodeSignal unit tests: add current directory into search path
import os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, os.path.dirname(currentdir))

import unittest
import time, datetime
import requests, urllib

from helpers import *
from helpers_hidden import *
import solution, runner

server = runner.ServerManager.create(solution.app)  # keep this!


SNIPPET = "hello, snippets!"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class TestBasicFunctionality(SnippetHiddenTestCase):
    def __init__(self, *a, **kw):
        super().__init__(server, *a, **kw)
        self._r = None

    #
    # Creation tests
    #

    def _create(self):
        self._r = post("snippets", json=make_request("basics"))
        self.assertIsNotNone(self._r)
        return self._r

    def test_creation_status_code_exact(self):
        r = self._create()
        self.assertEqual(201, r.status_code)

    #
    # Retrieval tests
    #

    def _retrieve(self):
        r = self._create()
        r = get("snippets/basics")
        self.assertIsNotNone(r)
        return r

    def test_retrieval_status_code(self):
        r = self._retrieve()
        self.assertEqual(200, r.status_code, r.text)
        return r

    def test_retrieval_schema_values(self):
        r = self.test_retrieval_status_code()
        js = self._get_js(r)

        for field in ("name", "snippet", "url", "expires_at"):
            self.assertIn(field, js.keys())
            self.assertIsInstance(js[field], str)

        self.assertEqual("basics", js["name"])
        self.assertEqual(SNIPPET, js["snippet"])
        return js

    def test_retrieval_schema_time(self):
        js = self.test_retrieval_schema_values()
        expires_at = js["expires_at"]
        try:
            return datetime.datetime.strptime(expires_at, DATE_FORMAT)
        except:
            self.fail("bad time: " + repr(expires_at))
        return expires_at

    def test_retrieval_schema_path(self):
        js = self.test_retrieval_schema_values()

        # best way to check validity: actually use it!
        try:
            new_js = requests.get(js["url"]).json()
        except:
            self.fail("invalid/inaccessible 'url' field")

        js.pop("expires_at")
        new_js.pop("expires_at")  # by querying we change this field

        self.assertEqual(js, new_js)

    def test_retrieval_refresh(self):
        expires_at = self.test_retrieval_schema_time()

        # dirty retrieval of the original expiration time, if it fails then
        # earlier tests failed
        try:
            expired_at = self._r.json()["expires_at"]
            expired_at = datetime.datetime.strptime(expired_at, DATE_FORMAT)

        except:
            self.fail("getting original expiration time failed")

        delta = expires_at - expired_at
        self.assertAlmostEqual(
            delta.seconds + delta.microseconds,
            5,
            delta=0.25,
            msg="expected +5s from %s but got %s" % (expired_at, expires_at),
        )

    def test_retrieval_expiration(self):
        self._create()
        time.sleep(2.25)
        r = get("snippet/basics")
        self.assertIsNotNone(r)
        self.assertEqual(404, r.status_code, "expected 404 got " + r.text)


class TestEdgeCases(SnippetHiddenTestCase):
    def __init__(self, *a, **kw):
        super().__init__(server, *a, **kw)

    def test_special_characters(self):
        specials = [
            "$",
            "&",
            "+",
            ",",
            "/",
            ":",
            ";",
            "=",
            "?",
            "@",
            "<",
            ">",
            "#",
            "%",
            "{",
            "}",
            "|",
            "^",
            "~",
            "[",
            "]",
            "`",  # 22 total
        ]

        for c in specials:
            with self.subTest(char=c):
                name = "this%cis%ca%cname" % ((c,) * 3)

                r = post("snippets", json=make_request(name))
                self.assertIsNotNone(r)
                self.is_http_success(r.status_code)

                try:
                    js = r.json()
                except:
                    self.fail("bad json")

                for field in ("name", "url"):
                    self.assertIn(field, js.keys())

                self.assertEqual(name, js["name"])
                self.assertIn(urllib.parse.quote(name, safe=""), js["url"])

    def _double_post(self):
        r = post("snippets", json=make_request("basics"))
        self.assertIsNotNone(r)
        r = post("snippets", json=make_request("basics"))
        self.assertIsNotNone(r)
        return r

    def test_errors_conflict(self):
        r = self._double_post()
        self.assertEqual(409, r.status_code)

    def test_errors_conflict_partial(self):
        r = self._double_post()
        self.is_http_error(r.status_code)


class TestMalformedInputs(SnippetHiddenTestCase):
    def __init__(self, *a, **kw):
        super().__init__(server, *a, **kw)
        self.request = make_request("malformed")

    def _run(self, request):
        r = post("snippets", json=request)
        self.assertIsNotNone(r)
        self.is_http_error(r.status_code)

    def test_bad_name(self):
        malformed = self.request.copy()
        malformed["name"] = 0xDEADBEEF
        self._run(malformed)

    def test_bad_expiration(self):
        malformed = self.request.copy()
        malformed["expires_in"] = "word"
        self._run(malformed)

    def test_bad_snippet(self):
        malformed = self.request.copy()
        malformed["snippet"] = 0xCAFEBABE
        self._run(malformed)


def make_request(name, exp=2):
    return {
        "name": name,
        "expires_in": exp,
        "snippet": SNIPPET,
    }