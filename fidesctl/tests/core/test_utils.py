import os

from fidesctl.core.config import config

import pytest

from fidesctl.core import utils


@pytest.mark.unit
def test_get_db_engine():
    conn_str = config.get_config().api.database_url
    engine = utils.get_db_engine(conn_str)
    assert str(engine.url) == conn_str
