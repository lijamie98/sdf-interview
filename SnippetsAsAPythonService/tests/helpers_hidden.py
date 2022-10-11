# This contains additional helpers for hidden test cases.
#
# NOTE: We don't lock `helpers.py` so the candidate could pull off some
#       shenanigans by modifying the SnippetTestCase base class, but hopefully
#       that either (a) never happens or (b) gets caught by manual grading.
#
# We can lock it in the future; it's just unlocked now for easier debugging from
# an evaluator's perspective.

import unittest
import logging
import click

import requests

from helpers import SnippetTestCase


class SnippetHiddenTestCase(SnippetTestCase):
    """This contains helpers for testing and also disables logging."""

    def __init__(self, server, *args, **kwargs):
        super().__init__(server, *args, **kwargs)
        logging.getLogger("werkzeug").disabled = True
        click.echo = click.secho = lambda text, **kwargs: None

    def _get_js(self, request):
        try:
            js = request.json()
            self.assertIsNotNone(js)
            return js
        except:
            self.fail("bad json:" + request.text)

    def is_http_success(self, code):
        self.assertGreaterEqual(code, 200, "expected 2xx got %d" % code)
        self.assertLess(code, 300, "expected 2xx got %d" % code)

    def is_http_error(self, code):
        self.assertGreaterEqual(code, 400, "expected 4xx got %d" % code)
        self.assertLess(code, 500, "expected 4xx got %d" % code)