import pytest

from fides.core.user import Credentials

@pytest.mark.unit
class TestCredentials:
    """
    Test the Credentials object.
    """
    def test_valid_credentials(self):
        credentials = Credentials(username="test", password="password", user_id="some_id",access_token="some_token")
        assert credentials.username == "test"
        assert credentials.password == "password"
        assert credentials.user_id == "some_id"
        assert credentials.access_token == "some_token"
