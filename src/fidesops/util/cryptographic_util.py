import hashlib
import secrets
from base64 import b64decode, b64encode

import bcrypt

from fidesops.core.config import config


def hash_with_salt(text: bytes, salt: bytes) -> str:
    """Hashes the text using SHA-512 with the provided salt and returns the hex string
    representation"""
    return hashlib.sha512(text + salt).hexdigest()


def generate_secure_random_string(length: int) -> str:
    """Generates a securely random string using Python secrets library
    that is twice the length of the specified input"""
    return secrets.token_hex(length)


def generate_salt() -> str:
    """Generates a salt using bcrypt and returns a string using the configured default encoding"""
    return bcrypt.gensalt().decode(config.security.ENCODING)


def bytes_to_b64_str(bytestring: bytes) -> str:
    """Converts random bytes into a utf-8 encoded string"""
    return b64encode(bytestring).decode(config.security.ENCODING)


def b64_str_to_bytes(encoded_str: str) -> bytes:
    """Converts encoded string into bytes"""
    return b64decode(encoded_str.encode(config.security.ENCODING))
