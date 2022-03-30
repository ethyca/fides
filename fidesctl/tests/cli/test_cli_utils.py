import importlib
from unittest.mock import patch

import pytest
import requests

import fidesctl.cli.utils as utils


@pytest.mark.unit
def test_check_server_bad_ping():
    "Check for an exception if the server isn't up."
    with pytest.raises(requests.exceptions.ConnectionError):
        utils.check_server("foo", "http://fake_address:8080")


@pytest.mark.integration
def test_check_server_version_mismatch(test_config):
    "Check for a warning message if there is a version mismatch."
    with patch("fidesctl.core.utils.echo_red") as echo_red_mock:
        # Reload the lib so that it picks up the mocked function
        importlib.reload(utils)
        utils.check_server("0.0.1", test_config.cli.server_url)
        echo_red_mock.assert_called_once()
