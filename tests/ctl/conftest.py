"""This file is only for the database fixture. For all other fixtures add them to the
tests/conftest.py file.
"""

import pytest
import requests
from pytest import MonkeyPatch

from fides.api.ctl.database.session import sync_engine, sync_session
from fides.core import api
from tests.conftest import create_citext_extension

orig_requests_get = requests.get
orig_requests_post = requests.post
orig_requests_put = requests.put
orig_requests_patch = requests.patch
orig_requests_delete = requests.delete


@pytest.fixture(scope="session")
def monkeysession():
    """
    Monkeypatch at the session level instead of the function level.
    Automatically undoes the monkeypatching when the session finishes.
    """
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(autouse=True, scope="session")
def monkeypatch_requests(test_client, monkeysession) -> None:
    """
    Some places within the application, for example `fides.core.api`, use the `requests`
    library to interact with the webserver. This fixture patches those `requests` calls
    so that all of those tests instead interact with the test instance.
    """
    monkeysession.setattr(requests, "get", test_client.get)
    monkeysession.setattr(requests, "post", test_client.post)
    monkeysession.setattr(requests, "put", test_client.put)
    monkeysession.setattr(requests, "patch", test_client.patch)
    monkeysession.setattr(requests, "delete", test_client.delete)


@pytest.fixture(scope="session", autouse=True)
@pytest.mark.usefixtures("monkeypatch_requests")
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


@pytest.fixture
def db():
    create_citext_extension(sync_engine)

    session = sync_session()

    yield session
    session.close()
