import pytest
import requests

from fides.api.ctl.database.session import sync_engine, sync_session
from fides.core import api
from tests.conftest import create_citext_extension


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
