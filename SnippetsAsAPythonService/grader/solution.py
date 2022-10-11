from typing import Tuple, Dict
from flask import Flask, request

# Do not modify this line or any function signatures.
app = Flask(__name__)


import time, datetime
import functools
import json, urllib
import hashlib, binascii


database = {}
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def get_json(**kwargs) -> Dict:
    """Forcibly returns the request data as JSON, `None` otherwise."""
    return request.get_json(force=True, **kwargs)


def validate_make_snippet(request: Dict, required=True):
    """Validates that the given JSON conforms to the creation schema.

    Assumption: `expires_in` must be non-negative, can be floating point.
    """
    keys = ("name", "expires_in", "snippet")
    types = (str, (float, int), str)
    for (field, types) in zip(keys, types):
        if field not in request and required:
            return False
        if field in request and not isinstance(request[field], types):
            return False

    if request.get("expires_in", 1) <= 0:
        return False

    # password is optional
    password = request.get("password", None)
    if password and not isinstance(password, str):
        return False

    return *tuple(map(request.get, keys)), password


def validate_edit_request(request: dict):
    """Validates that the given JSON conforms to the editing schema."""
    rv = validate_make_snippet(request, required=False)
    if not rv:
        return False
    # password is not optional
    return rv if rv[-1] else False


def hash(s: str) -> str:
    """Uses Blake2s (bcrypt would be ideal but it isn't built-in to hash."""
    digest = hashlib.blake2s(s.encode("utf8")).digest()
    for _ in range(5):  # to slow down "attackers"
        digest = hashlib.blake2s(digest).digest()

    return binascii.hexlify(digest)


class Snippet:
    def __init__(self, name, expires_in, content):
        self.name = name
        self.expires_at = datetime.datetime.now()
        self.expires_at += datetime.timedelta(seconds=expires_in)
        self.snippet = content
        self.password_hash = None
        self.likes = 0

        self.url = request.url + urllib.parse.quote(self.name, safe="")

    def secure(self, password):
        if not password:
            return
        self.password_hash = hash(password)

    def update(self):
        self.expires_at += datetime.timedelta(seconds=5)
        return self

    def like(self):
        self.likes += 1
        return self.update()

    def is_editable(self, password):
        return not self.password_hash or self.password_hash == hash(password)

    def edit(self, new_name, new_content, new_expiration_delta):
        if new_expiration_delta:
            self.expires_at += datetime.timedelta(seconds=new_expiration_delta)
        else:
            self.update()

        self.snippet = new_content
        self.name = new_name

    @property
    def expired(self):
        return self.expires_at < datetime.datetime.now()

    @property
    def json(self):
        js = {
            "name": self.name,
            "expires_at": self.expires_at.strftime(DATE_FORMAT),
            "snippet": self.snippet,
            "url": self.url,
            "likes": self.likes,
            "secure": bool(self.password_hash),
        }
        return js


#
# Routes follow
#


@app.route("/snippets/", methods=["POST"])
def make_snippet() -> Tuple[Dict, int]:
    """Process & validate a new snippet.

    Return the response bytes (for example, marshaled JSON) and an appropriate
    HTTP status code.
    """
    js = get_json()

    valid = validate_make_snippet(js)
    if not valid:
        return {"error": "Invalid JSON"}, 400
    name, expiration, snippet, password = valid

    if name in database:
        return {"error": "Snippet already exists"}, 409

    snippet = Snippet(name, expiration, snippet)
    snippet.secure(password)

    database[name] = snippet
    return snippet.json, 201


@app.route("/snippets/<name>/", methods=["GET"])
def get_snippet(name: str) -> Tuple[Dict, int]:
    """Process requests for a snippet by a name.

    It correponds to `GET /snippets/<name>`.

    Like `make_snippet()`, it should return the response bytes and an
    appropriate HTTP status code.
    """
    snippet = database.pop(name, None)
    if snippet is None or snippet.expired:
        return {"error": f"{name} does not exist"}, 404

    database[name] = snippet.update()
    return snippet.json, 200


@app.route("/snippets/<name>/like/", methods=["POST"])
def like_snippet(name: str) -> Tuple[Dict, int]:
    """Process a like request to a snippet by name.

    It correponds to `POST /snippets/<name>/like`.
    """
    snippet = database.pop(name, None)
    if snippet is None or snippet.expired:
        return {"error": f"{name} does not exist"}, 404

    database[name] = snippet.like()
    return snippet.json, 200
