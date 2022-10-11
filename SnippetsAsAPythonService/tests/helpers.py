import unittest
import requests


class SnippetTestCase(unittest.TestCase):
    """A shim to start and stop the web server for every test case."""

    def __init__(self, server, *args, **kwargs):
        self.server = server
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.server.start()

    def tearDown(self):
        self.server.stop()


HOST, PORT = "localhost", 8080
BASE_URL = f"http://{HOST}:{PORT}/"

# shorthand for easier testing


def post(url="", **kwargs):
    try:
        return requests.post(BASE_URL + url, **kwargs)
    except:
        return None


def put(url="", **kwargs):
    try:
        return requests.put(BASE_URL + url, **kwargs)
    except:
        return None


def get(url="", **kwargs):
    try:
        return requests.get(BASE_URL + url, **kwargs)
    except:
        return None