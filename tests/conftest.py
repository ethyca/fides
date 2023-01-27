import pytest
from loguru import logger

from fides.core.config import get_config


@pytest.fixture(scope="session")
def config():
    config = get_config()
    config.is_test_mode = True
    yield config


@pytest.fixture
def loguru_caplog(caplog):
    handler_id = logger.add(caplog.handler, format="{message}")
    yield caplog
    logger.remove(handler_id)
