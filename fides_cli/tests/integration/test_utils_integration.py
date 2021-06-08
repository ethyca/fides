import pytest

from fides.core import utils


def test_get_db_engine():
    conn_str = "mysql+mysqlconnector://fidesdb:fidesdb@fides-db:3306/fidesdb"
    engine = utils.get_db_engine(conn_str)
    assert str(engine.url) == conn_str
