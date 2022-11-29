# pylint: disable=missing-function-docstring, redefined-outer-name

from copy import deepcopy

import pytest
from fides.lib.db.session import get_db_engine, get_db_session
from fides.lib.exceptions import MissingConfig


@pytest.fixture
def config_no_database_uri(config):
    new_config = deepcopy(config)
    new_config.database.sqlalchemy_database_uri = None
    yield new_config


@pytest.fixture
def config_no_test(config):
    new_config = deepcopy(config)
    new_config.database.sqlalchemy_database_uri = (
        "postgresql://postgres:postgres@localhost:5432/prod"
    )
    new_config.is_test_mode = False
    yield new_config


def test_get_db_engine(config):
    database_uri = "postgresql://postgres@localhost:5432/test"
    engine = get_db_engine(config=config, database_uri=database_uri)

    # engine url gets masked so check the prefix and postfix
    assert str.startswith(str(engine.url), "postgresql")
    assert str.endswith(str(engine.url), "5432/test")


def test_get_db_engine_database_uri():
    database_uri = "postgresql://postgres@localhost:5432/test"
    engine = get_db_engine(database_uri=database_uri)

    # engine url gets masked so check the prefix and postfix
    assert str.startswith(str(engine.url), "postgresql")
    assert str.endswith(str(engine.url), "5432/test")


def test_get_db_engine_config_no_dev(config_no_test):
    engine = get_db_engine(config=config_no_test)
    print(config_no_test)

    assert "postgresql://postgres:postgres@localhost:5432/prod" in str(engine.url)


def test_get_db_engine_config_dev(config):
    engine = get_db_engine(config=config)

    assert "postgresql://postgres:postgres@localhost:5432/test" in str(engine.url)


def test_get_db_engine_no_param_error():
    with pytest.raises(ValueError):
        get_db_engine()


def test_get_db_session_no_database_uri(config_no_database_uri):
    with pytest.raises(MissingConfig):
        get_db_session(config_no_database_uri)
