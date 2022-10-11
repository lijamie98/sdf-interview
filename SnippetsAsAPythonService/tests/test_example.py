# required for CodeSignal unit tests: add current directory into search path
import os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import solution, runner, helpers

server = runner.ServerManager.create(solution.app)  # keep this!


class TestExample(helpers.SnippetTestCase):
    """Feel free to add your own test cases here.

    If you decide to overwrite setUp and tearDown, be sure to still call the
    superclass' methods.
    """

    def __init__(self, methodName="runTest"):
        super().__init__(server, methodName=methodName)

    def test_example(self):
        request = {
            "name": "name",
            "expires_in": 30,
            "snippet": "snippet",
        }

        response = helpers.post("snippets", json=request)
        self.assertNotEqual(response.status_code, 500)
        print(response.status_code)