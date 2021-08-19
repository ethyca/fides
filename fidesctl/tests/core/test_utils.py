import os

import pytest

from fidesctl.core import utils


@pytest.mark.unit
def test_get_db_engine():
    conn_str = os.getenv("FIDES_SERVER_SQLALCHEMY_CONN_STR", "")
    engine = utils.get_db_engine(conn_str)
    assert str(engine.url) == conn_str
