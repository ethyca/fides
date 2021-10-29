import hashlib
import secrets
import bcrypt

from fidesops.core.config import config


def hash_with_salt(text: bytes, salt: bytes) -> str:
    """Hashes the text using SHA-512 with the provided salt and returns the hex string
    representation"""
    return hashlib.sha512(text + salt).hexdigest()


def generate_secure_random_string(length_in_bytes: int) -> str:
    """Generates a securely random string using Python secrets library"""
    return secrets.token_hex(length_in_bytes)


def generate_salt() -> str:
    """Generates a salt using bcrypt and returns a string using the configured default encoding"""
    return bcrypt.gensalt().decode(config.security.ENCODING)
