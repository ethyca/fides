"""This file is only for the database fixture. For all other fixtures add them to the
tests/conftest.py file.
"""

import pytest
import requests
from fideslang import DEFAULT_TAXONOMY
from pytest import MonkeyPatch

from fides.api.db.ctl_session import sync_engine, sync_session
from fides.api.models.sql_models import DataUse
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
def setup_ctl_db(api_client, config):
    "Sets up the database for testing."
    assert config.test_mode
    assert requests.post != api_client.post
    yield api_client.post(url=f"{config.cli.server_url}/v1/admin/db/reset")


@pytest.fixture(scope="session")
def db():
    create_citext_extension(sync_engine)

    session = sync_session()

    yield session
    session.close()


@pytest.fixture(scope="function", autouse=True)
def load_default_data_uses(db):
    for data_use in DEFAULT_TAXONOMY.data_use:
        # Default data uses are cleared and not automatically reloaded by `clear_db_tables` fixture.
        # Here we make sure our default data uses are always available for our tests,
        # if they're not present already.
        if DataUse.get_by(db, field="name", value=data_use.name) is None:
            DataUse.create(db=db, data=data_use.model_dump(mode="json"))
