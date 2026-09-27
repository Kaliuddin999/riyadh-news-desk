import base64
import json
import os

import pytest
from cryptography.exceptions import InvalidTag

from newsdesk.crypto import ITERATIONS, decrypt_json, encrypt_json, load_or_create_salt

PW = "correct horse battery"


def test_round_trip_keeps_unicode():
    salt = os.urandom(16)
    blob = encrypt_json({"title": "Rain in Riyadh ⛈️"}, PW, salt, iterations=1000)
    assert decrypt_json(blob, PW) == {"title": "Rain in Riyadh ⛈️"}


def test_wrong_password_fails():
    blob = encrypt_json({"a": 1}, PW, os.urandom(16), iterations=1000)
    with pytest.raises(InvalidTag):
        decrypt_json(blob, "wrong password!!")


def test_blob_format_hides_content():
    salt = os.urandom(16)
    blob = encrypt_json({"secret": "Shalfa halt"}, PW, salt, iterations=1000)
    assert blob["v"] == 1 and blob["kdf"] == "PBKDF2-SHA256" and blob["iter"] == 1000
    assert base64.b64decode(blob["salt"]) == salt
    assert len(base64.b64decode(blob["iv"])) == 12
    text = json.dumps(blob)
    assert "Shalfa" not in text and PW not in text


def test_new_iv_every_time():
    salt = os.urandom(16)
    a = encrypt_json({"a": 1}, PW, salt, iterations=1000)
    b = encrypt_json({"a": 1}, PW, salt, iterations=1000)
    assert a["iv"] != b["iv"]


def test_salt_is_created_once(tmp_path):
    path = tmp_path / "data" / "salt.bin"
    first = load_or_create_salt(path)
    assert len(first) == 16
    assert load_or_create_salt(path) == first


def test_default_iterations():
    assert ITERATIONS == 600_000
