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


def test_user_create_user_name_with_spaces():
    with pytest.raises(ValueError):
        UserCreate(
            username="some user",
            password=str_to_b64_str("Testtest1!"),
            email_address="test.user@ethyca.com",
            first_name="test",
            last_name="test",
        )


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
