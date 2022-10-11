import multiprocessing
import unittest
import requests


# WARNING: Do NOT edit this file.
#
# CodeSignal runs tests in a single-threaded fashion, but we'd like to run your
# server in the background to do proper integration testing against it. As a
# result, it's necessary to run the server in a background thread, but only
# once. This module helps manage that process.

from helpers import HOST, PORT, BASE_URL

HELP = """\n\nUnless you are doing something erroneous in your tests like
calling setUp() twice, this is a test framework exception. Please report it to
the test administrators!
"""


class ServerManager:
    instance = None

    def __init__(self, app):
        self.app = app
        self._prepare_process()

    def start(self):
        """Starts the web server process then waits for it to be ready."""
        if self.process.is_alive():
            raise Exception(
                "Attempted to run server while it's already running." + HELP
            )

        self.process.start()

        for _ in range(10):  # retry until the server is ready
            try:
                requests.get(BASE_URL, timeout=1)
                break
            except requests.exceptions.ConnectionError:
                continue
        else:
            raise Exception("Failed to run the web server." + HELP)

    def stop(self):
        """Makes a best-effort attempt to stop the web server."""
        self.process.terminate()
        self.process.join(1)

        # retry more aggressively
        if self.process.exitcode is None:
            self.process.kill()
            self.process.join(1)

        if self.process.exitcode is None:
            raise Exception("Failed to stop the web server." + HELP)

        exitcode = self.process.exitcode
        self._prepare_process()
        return exitcode

    def _prepare_process(self):
        self.process = multiprocessing.Process(
            name="BackgroundWebServer",
            target=self.app.run,
            kwargs={"host": HOST, "port": PORT},
            daemon=True,
        )

    @staticmethod
    def create(app):
        if ServerManager.instance is None:
            ServerManager.instance = ServerManager(app)

        return ServerManager.instance