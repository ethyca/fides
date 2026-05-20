# pylint: disable=missing-function-docstring, redefined-outer-name

import pytest

from fides.api.cryptography.cryptographic_util import (
    b64_str_to_bytes,
    b64_str_to_str,
    bytes_to_b64_str,
    decode_password,
    generate_salt,
    generate_secure_random_string,
    hash_credential_with_salt,
    hash_value_with_salt,
    str_to_b64_str,
)


@pytest.fixture
def byte_string():
    yield b"foobar"


@pytest.fixture
def b64_encoded():
    yield "Zm9vYmFy"


def test_b64_str_to_bytes(b64_encoded, byte_string):
    assert b64_str_to_bytes(b64_encoded) == byte_string


def test_b64_str_to_str() -> None:
    b64_string = "aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbQ=="
    result = b64_str_to_str(b64_string)
    assert "https://www.google.com" == result


def test_bytes_to_b64_str(byte_string, b64_encoded):
    assert bytes_to_b64_str(byte_string) == b64_encoded


def test_bytes_to_b64_str_invalid_encoding():
    with pytest.raises(TypeError):
        bytes_to_b64_str("foobar")  # type: ignore


def test_generate_salt():
    # Generates unique salt strings
    generated = set()
    for _ in range(10):
        generated.add(generate_salt())

    assert len(generated) == 10


def test_generate_secure_random_string():
    bytelength = 26

    # Generates a random string with a hex length twice that of the given bytelength.
    assert len(generate_secure_random_string(bytelength)) == 2 * bytelength

    # Generates unique strings
    generated = set()
    for _ in range(10):
        generated.add(generate_secure_random_string(bytelength))

    assert len(generated) == 10


def test_hash_credential_with_salt(encoding: str = "UTF-8") -> None:
    plain_text = "This is Plaintext. Not hashed. or salted. or chopped. or grilled."
    salt = "$2b$12$JpqVneuGhHBN62Gh/b0EP."

    expected_hash = "243262243132244a7071566e6575476848424e363247682f623045502e626476724a63656c637274514e7450584d2e392e4d49647871507636337469"  # pylint: disable=C0301
    hashed = hash_credential_with_salt(
        plain_text.encode(encoding),
        salt.encode(encoding),
    )

    assert hashed == expected_hash


def test_hash_value_with_salt(encoding: str = "UTF-8") -> None:
    plain_text = "This is Plaintext. Not hashed. or salted. or chopped. or grilled."
    salt = "$2b$12$JpqVneuGhHBN62Gh/b0EP."

    expected_hash = "1be641a0a1693ea040f2a48b12c43b1b6bd13025b0ce7fd7e244abe7c849625a"  # pylint: disable=C0301
    hashed = hash_value_with_salt(
        plain_text.encode(encoding),
        salt.encode(encoding),
    )

    assert hashed == expected_hash


def test_str_to_b64_str() -> None:
    orig_string = "https://www.google.com"
    b64_string = "aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbQ=="
    result = str_to_b64_str(orig_string)
    assert b64_string == result


@pytest.mark.parametrize(
    "password, expected",
    [
        ("Testpassword1!", "Testpassword1!"),
        (
            "Test_1234",
            "Test_1234",
        ),  # this is actually valid base64 (but should be treated as plaintext), so this represents an edge case
        (str_to_b64_str("Testpassword1!"), "Testpassword1!"),
        (str_to_b64_str("Test_1234"), "Test_1234"),
    ],
)
def test_decode_password(password, expected):
    assert decode_password(password) == expected
