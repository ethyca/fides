import pytest

from fidesops.api.deps import get_cache, get_db
from fidesops.common_exceptions import FunctionalityNotConfigured
from fidesops.core import config


@pytest.fixture
def mock_config():
    db_enabled = config.config.database.enabled
    redis_enabled = config.config.redis.enabled
    config.config.database.enabled = False
    config.config.redis.enabled = False
    yield
    config.config.database.enabled = db_enabled
    config.config.redis.enabled = redis_enabled


@pytest.mark.usefixtures("mock_config")
def test_get_cache_not_enabled():
    with pytest.raises(FunctionalityNotConfigured):
        next(get_cache())


@pytest.mark.usefixtures("mock_config")
def test_get_db_not_enabled():
    with pytest.raises(FunctionalityNotConfigured):
        next(get_db())
