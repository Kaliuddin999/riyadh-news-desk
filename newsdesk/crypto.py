"""Password-based encryption compatible with the browser's Web Crypto API."""
import base64
import json
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 600_000


def load_or_create_salt(path):
    """The salt is not secret; it is kept stable so devices can remember the derived key."""
    if path.exists():
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    salt = os.urandom(16)
    path.write_bytes(salt)
    return salt


def _key(password, salt, iterations):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return kdf.derive(password.encode("utf-8"))


def _b64(data):
    return base64.b64encode(data).decode("ascii")


def encrypt_json(obj, password, salt, iterations=ITERATIONS):
    iv = os.urandom(12)
    plain = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    ct = AESGCM(_key(password, salt, iterations)).encrypt(iv, plain, None)
    return {"v": 1, "kdf": "PBKDF2-SHA256", "iter": iterations,
            "salt": _b64(salt), "iv": _b64(iv), "ct": _b64(ct)}


def decrypt_json(blob, password):
    key = _key(password, base64.b64decode(blob["salt"]), blob["iter"])
    plain = AESGCM(key).decrypt(base64.b64decode(blob["iv"]), base64.b64decode(blob["ct"]), None)
    return json.loads(plain.decode("utf-8"))
