from os import environ

import pytest

from fides.core.user import (
    Credentials,
    get_auth_header,
    get_credentials_path,
    read_credentials_file,
)


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
        assert credentials.user_id == "some_id"
        assert credentials.access_token == "some_token"


def test_get_credentials_path() -> None:
    """Test that a custom path for the credentials file works as expected."""
    expected_path = "test_credentials"
    environ["FIDES_CREDENTIALS_PATH"] = expected_path
    actual_path = get_credentials_path()
    assert expected_path == actual_path


def test_read_credentials_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        credentials = read_credentials_file(credentials_path="notarealfile")
        print(credentials)


def test_get_auth_header_file_not_found():
    """
    Verify that a SystemExit is raised when a credentials file
    can't be found.

    Additionally, use the `verbose` flag to make sure that code
    path is also covered.
    """
    environ["FIDES_CREDENTIALS_PATH"] = "thisfiledoesnotexist"
    with pytest.raises(SystemExit):
        header = get_auth_header(verbose=True)
        print(header)
