import pytest
from loguru import logger
from sqlalchemy.engine.base import Engine

from fides.core.config import CONFIG


@pytest.fixture(scope="session")
def config():

    config.is_test_mode = True
    yield config


@pytest.fixture
def loguru_caplog(caplog):
    handler_id = logger.add(caplog.handler, format="{message}")
    yield caplog
    logger.remove(handler_id)


def create_citext_extension(engine: Engine) -> None:
    with engine.connect() as con:
        con.execute("CREATE EXTENSION IF NOT EXISTS citext;")
