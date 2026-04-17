# pylint: disable=missing-function-docstring

import pytest
from pydantic import ValidationError

from fides.api.cryptography.cryptographic_util import str_to_b64_str
from fides.api.schemas.user import UserCreate, UserLogin


@pytest.mark.parametrize(
    "password, message",
    [
        ("Short1!", "eight characters"),
        ("Nonumber*", "one number"),
        ("nocapital1!", "one capital"),
        ("NOLOWERCASE1!", "one lowercase"),
        ("Nosymbol1", "one symbol"),
    ],
)
def test_bad_password(password, message):
    with pytest.raises(ValueError) as excinfo:
        UserCreate(
            username="test",
            password=str_to_b64_str(password),
            email_address="test.user@ethyca.com",
            first_name="test",
            last_name="test",
        )

    assert message in str(excinfo.value)


@pytest.mark.parametrize(
    "username",
    [
        "some user",
        "user&name",
        "user=name",
        "user<name",
        "user@name",
        "",
        "a" * 101,
    ],
)
def test_user_create_invalid_username(username):
    with pytest.raises(ValueError):
        UserCreate(
            username=username,
            password=str_to_b64_str("Testtest1!"),
            email_address="test.user@ethyca.com",
            first_name="test",
            last_name="test",
        )


@pytest.mark.parametrize(
    "username",
    [
        "testuser",
        "test-user",
        "test_user",
        "Test_User-123",
        "john.doe",
        "a",
        "a" * 100,
    ],
)
def test_user_create_valid_username(username):
    user = UserCreate(
        username=username,
        password=str_to_b64_str("Testtest1!"),
        email_address="test.user@ethyca.com",
        first_name="test",
        last_name="test",
    )
    assert user.username == username


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            username="user",
            password=str_to_b64_str("Testtest1!"),
            email_address="NotAnEmailAddress",
            first_name="test",
            last_name="test",
        )


@pytest.mark.parametrize(
    "password, expected",
    [
        ("Testpassword1!", "Testpassword1!"),
        (str_to_b64_str("Testpassword1!"), "Testpassword1!"),
    ],
)
def test_user_create(password, expected):
    user = UserCreate(
        username="immauser",
        password=password,
        email_address="test.user@ethyca.com",
        first_name="imma",
        last_name="user",
    )

    assert user.password == expected


@pytest.mark.parametrize(
    "password, expected",
    [
        ("Testpassword1!", "Testpassword1!"),
        (str_to_b64_str("Testpassword1!"), "Testpassword1!"),
    ],
)
def test_user_login(password, expected):
    user = UserLogin(username="immauser", password=password)

    assert user.password == expected
