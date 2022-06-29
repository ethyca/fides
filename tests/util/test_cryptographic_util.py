from fidesops.core.config import config
from fidesops.util.cryptographic_util import (
    b64_str_to_bytes,
    b64_str_to_str,
    bytes_to_b64_str,
    hash_with_salt,
    str_to_b64_str,
)


def test_hash_with_salt() -> None:
    plain_text = "This is Plaintext. Not hashed. or salted. or chopped. or grilled."
    salt = "adobo"

    expected_hash = "3318b888645e6599289be9bee8ac0af2e63eb095213b7269f84845303abde55c7c0f9879cd69d7f453716e439ba38dd8d9b7f0bec67fe9258fb55d90e94c972d"
    hashed = hash_with_salt(
        plain_text.encode(config.security.ENCODING),
        salt.encode(config.security.ENCODING),
    )

    assert hashed == expected_hash


def test_bytes_to_b64_str() -> None:
    byte_string = b"https://www.google.com"
    b64_string = "aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbQ=="
    result = bytes_to_b64_str(byte_string)
    assert b64_string == result


def test_b64_str_to_bytes() -> None:
    b64_string = "aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbQ=="
    result = b64_str_to_bytes(b64_string)
    assert b"https://www.google.com" == result


def test_b64_str_to_str() -> None:
    b64_string = "aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbQ=="
    result = b64_str_to_str(b64_string)
    assert "https://www.google.com" == result


def test_str_to_b64_str() -> None:
    orig_string = "https://www.google.com"
    b64_string = "aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbQ=="
    result = str_to_b64_str(orig_string)
    assert b64_string == result
