# pylint: disable=duplicate-code, missing-function-docstring

from unittest.mock import MagicMock

import pytest

from fides.api.models.fides_user import FidesUser


def test_create_user():
    password = "test_password"
    user = FidesUser.create(
        db=MagicMock(),
        data={"username": "user_1", "password": password},
    )

    assert user.username == "user_1"
    assert user.hashed_password != "test_password"
    assert not user.credentials_valid("bad_password")
    assert user.credentials_valid(password)


def test_create_user_bad_payload():
    with pytest.raises(KeyError):
        FidesUser.create(
            db=MagicMock(),
            data={},
        )


def test_update_user_password():
    password = "test_password"
    user = FidesUser.create(
        db=MagicMock(),
        data={"username": "user_1", "password": password},
    )

    assert user.username == "user_1"
    assert user.password_reset_at is None
    assert user.credentials_valid(password)

    new_password = "new_test_password"
    user.update_password(MagicMock(), new_password)

    assert user.username == "user_1"
    assert user.password_reset_at is not None
    assert user.credentials_valid(new_password)
    assert user.hashed_password != new_password
    assert not user.credentials_valid(password)
