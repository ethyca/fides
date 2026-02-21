"""This file is only for the database fixture. For all other fixtures add them to the
tests/conftest.py file.
"""

import pytest
import requests

from fides.core import api

orig_requests_get = requests.get
orig_requests_post = requests.post
orig_requests_put = requests.put
orig_requests_patch = requests.patch
orig_requests_delete = requests.delete


@pytest.fixture(autouse=True, scope="session")
def _ctl_monkeypatch_requests(monkeypatch_requests):
    """Ensure all ctl tests have requests patched to use TestClient."""
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
