from os import environ
from unittest.mock import patch

import pytest

from fides.core.user import Credentials, get_credentials_path, get_auth_header


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


@patch.dict(
    environ,
    {
        "FIDES_CREDENTIALS_PATH": "/fides/somefakefile",
    },
    clear=True,
)
def test_get_auth_header_file_not_found():
    """
    Verify that a SystemExit is raised when a credentials file
    can't be found.

    Additionally, use the `verbose` flag to make sure that code
    path is also covered.
    """
    with pytest.raises(SystemExit):
        get_auth_header(verbose=True)
