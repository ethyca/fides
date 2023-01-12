from os import environ

import pytest

from fides.core.user import Credentials, get_credentials_path


@pytest.mark.unit
class TestCredentials:
    """
    Test the Credentials object.
    """

    def test_valid_credentials(self):
        credentials = Credentials(
            username="test",
            password="password",
            user_id="some_id",
            access_token="some_token",
        )
        assert credentials.username == "test"
        assert credentials.password == "password"
        assert credentials.user_id == "some_id"
        assert credentials.access_token == "some_token"


def test_get_credentials_path() -> None:
    """Test that a custom path for the credentials file works as expected."""
    expected_path = "test_credentials"
    environ["FIDES_CREDENTIALS_PATH"] = "test_credentials"
    actual_path = get_credentials_path()
    assert expected_path == actual_path
