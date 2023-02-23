import pytest
from loguru import logger
from sqlalchemy.engine.base import Engine

from fides.core.config import get_config


@pytest.fixture(scope="session")
def config():
    config = get_config()
    config.test_mode = True
    yield config


@pytest.fixture
def loguru_caplog(caplog):
    handler_id = logger.add(caplog.handler, format="{message}")
    yield caplog
    logger.remove(handler_id)


def create_citext_extension(engine: Engine) -> None:
    with engine.connect() as con:
        con.execute("CREATE EXTENSION IF NOT EXISTS citext;")
