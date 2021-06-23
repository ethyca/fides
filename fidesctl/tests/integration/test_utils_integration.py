import os

from fidesctl.core import utils


def test_get_db_engine():
    conn_str = os.getenv("FIDES_SERVER_SQLALCHEMY_CONN_STR")
    engine = utils.get_db_engine(conn_str)
    assert str(engine.url) == conn_str
