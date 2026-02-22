"""This file is only for the database fixture. For all other fixtures add them to the
tests/conftest.py file.
"""

import pytest
import requests

from fides.core import api
from fides.core.user import login_command
from fides.core.utils import get_auth_header

orig_requests_get = requests.get
orig_requests_post = requests.post
orig_requests_put = requests.put
orig_requests_patch = requests.patch
orig_requests_delete = requests.delete


@pytest.fixture(autouse=True, scope="session")
def _ctl_monkeypatch_and_login(monkeypatch_requests, config):
    """Ensure all ctl tests have requests patched to use TestClient,
    and perform a fides user login so config.user.auth_header is valid."""
    server_url = config.cli.server_url
    try:
        login_command(
            username=config.security.root_username,
            password=config.security.root_password,
            server_url=server_url,
        )
        config.user.auth_header = get_auth_header()
    except Exception:
        pass
    yield


@pytest.fixture(scope="session")
def setup_ctl_db(test_config, test_client, config):
    "Sets up the database for testing."
    assert config.test_mode
    assert (
        requests.post == test_client.post
    )  # Sanity check to make sure monkeypatch_requests fixture has run
    yield api.db_action(
        server_url=test_config.cli.server_url,
        headers=config.user.auth_header,
        action="reset",
    )
