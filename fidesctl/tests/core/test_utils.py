import os

from fidesctl.core.config import get_config

import pytest

from fidesctl.core import utils


@pytest.mark.unit
def test_get_db_engine():
    conn_str = get_config().api.sync_database_url
    engine = utils.get_db_engine(conn_str)
    assert str(engine.url) == conn_str
