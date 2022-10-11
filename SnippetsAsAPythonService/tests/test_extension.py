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


class TestLikeExtension(SnippetHiddenTestCase):
    def __init__(self, *a, **kw):
        super().__init__(server, *a, **kw)

    def test_like_creation(self):
        r = post("snippets", json=make_request("basics"))
        self.assertIsNotNone(r)
        return r

    def test_like_schema(self):
        r = self.test_like_creation()
        js, _ = self._validate_schema(r)
        self.assertEqual(0, js["likes"])

        r = get("snippets/basics")
        js, _ = self._validate_schema(r)
        self.assertEqual(0, js["likes"])

    def test_like_count(self):
        r = self.test_like_creation()
        _, expired_at = self._validate_schema(r)

        for like_count in range(1, 6):
            r = post("snippets/basics/like")
            self.assertIsNotNone(r)
            self.is_http_success(r.status_code)

            js, _ = self._validate_schema(r)
            self.assertEqual(like_count, js["likes"])

        r = get("snippets/basics")
        js, expires_at = self._validate_schema(r)
        self.assertEqual(like_count, js["likes"])

        return expires_at, expired_at

    def test_like_expiration(self):
        expires_at, expired_at = self.test_like_count()

        # after 5 likes with +5s each, then +5s for the GET,
        # we should expire 30s later than the orig
        delta = expires_at - expired_at
        self.assertAlmostEqual(
            delta.seconds + delta.microseconds,
            30,
            msg="expected +30s to %s (+/- 0.25s) but got %s" % (expired_at, expires_at),
            delta=0.25,
        )

    def _validate_schema(self, r):
        js = self._get_js(r)

        for field in ("name", "snippet", "url", "expires_at"):
            self.assertIn(field, js)
            self.assertIsInstance(js[field], str)

        self.assertIn("likes", js, repr(js))
        self.assertIsInstance(js["likes"], int)

        self.assertEqual("basics", js["name"])
        self.assertEqual(SNIPPET, js["snippet"])

        expires_at = js["expires_at"]
        try:
            expires_at = datetime.datetime.strptime(expires_at, DATE_FORMAT)
        except:
            self.fail("bad time: " + repr(expires_at))

        return js, expires_at


class TestEditExtension:
    """THESE TESTS ARE UNUSED.

    We should keep them around if we decide to allow the "edit" extension in the
    future rather than requiring the "likes" one.

    (To put them back, make this inherit from `SnippetHiddenTestCase`.)
    """

    def __init__(self, *a, **kw):
        super().__init__(server, *a, **kw)
        self.skip = False

    def setUp(self):
        if solution.EXTENSION_CHOICE != "edits":
            self.skip = True  # don't double-punish
        else:
            super().setUp()

    def tearDown(self):
        if not self.skip:
            super().tearDown()

    def test_password_not_required(self):
        if self.skip:
            return
        r = post("snippets", json=make_request("basics"))
        self.assertIsNotNone(r)
        self.is_http_success(r.status_code)
        return r

    def test_password_allowed(self):
        if self.skip:
            return
        r = post("snippets", json=make_request("basics", password="hunter2"))
        self.assertIsNotNone(r)
        self.is_http_success(r.status_code)
        return r

    def test_no_password_in_reply(self):
        if self.skip:
            return
        r = self.test_password_allowed()
        self.assertNotIn(r.text, "hunter2")

    def test_edit_schema(self):
        if self.skip:
            return
        r = self.test_password_allowed()
        js, _ = self._validate_schema(r)
        self.assertTrue(js["secure"], repr(js))

        r = post("snippets", json=make_request("basics-dupe"))
        js, _ = self._validate_schema(r, name="basics-dupe")
        self.assertFalse(js["secure"], repr(js))

    def _checks_password(self, password):
        r = self.test_password_allowed()
        r = post(
            "snippets/basics", json=make_edit_request("basics", password, "new content")
        )

        self.assertIsNotNone(r)
        self.assertTrue(
            self.is_http_error(r.status_code), "expected 4xx got %d" % r.status_code
        )

    def test_no_passwordless_edits(self):
        if self.skip:
            return
        return self._checks_password("")

    def test_no_bad_password_edits(self):
        if self.skip:
            return
        return self._checks_password("hunter3")

    def test_bad_password_status(self):
        if self.skip:
            return
        self.test_password_allowed()
        r = post(
            "snippets/basics", json=make_edit_request("basics", "bad", "new content")
        )
        self.assertIsNotNone(r)
        self.assertEqual(403, r.status_code)  # 4xx gets partial credit

    def test_can_edit(self):
        if self.skip:
            return
        r = self.test_password_allowed()
        r = post(
            "snippets/basics",
            json=make_edit_request("basics", "hunter2", "new content"),
        )
        self.assertIsNotNone(r)

        # response has edits
        js, _ = self._validate_schema(r, snippet="new content")
        self.assertTrue(js["secure"], repr(js))

        # so does a fresh GET
        r = get("snippets/basics")
        self.assertIsNotNone(r)
        js, _ = self._validate_schema(r, snippet="new content")
        self.assertTrue(js["secure"], repr(js))

    def _validate_schema(self, r, name="basics", snippet=SNIPPET):
        js = self._get_js(r)

        for field in ("name", "snippet", "url", "expires_at"):
            self.assertIn(field, js)
            self.assertIsInstance(js[field], str)

        self.assertIn("secure", js, repr(js))
        self.assertIsInstance(js["secure"], bool)

        self.assertEqual(name, js["name"])
        self.assertEqual(snippet, js["snippet"])

        expires_at = js["expires_at"]
        try:
            expires_at = datetime.datetime.strptime(expires_at, DATE_FORMAT)
        except:
            self.fail("bad time: " + repr(expires_at))

        return js, expires_at


def make_request(name, exp=2, password=None):
    request = {
        "name": name,
        "expires_in": exp,
        "snippet": SNIPPET,
    }
    if password:
        request["password"] = password
    return request


def make_edit_request(name, password, new_snippet):
    return {
        "name": name,
        "snippet": new_snippet,
        "password": password,
    }