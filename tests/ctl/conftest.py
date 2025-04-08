"""This file is only for the database fixture. For all other fixtures add them to the
tests/conftest.py file.
"""

import pytest
import requests
from fideslang import DEFAULT_TAXONOMY

from fides.api.models.sql_models import DataUse
from fides.core import api

orig_requests_get = requests.get
orig_requests_post = requests.post
orig_requests_put = requests.put
orig_requests_patch = requests.patch
orig_requests_delete = requests.delete


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="function")
def load_default_data_uses(db):
    for data_use in DEFAULT_TAXONOMY.data_use:
        # Default data uses are cleared and not automatically reloaded by `clear_db_tables` fixture.
        # Here we make sure our default data uses are always available for our tests,
        # if they're not present already.
        if DataUse.get_by(db, field="name", value=data_use.name) is None:
            DataUse.create(db=db, data=data_use.model_dump(mode="json"))
