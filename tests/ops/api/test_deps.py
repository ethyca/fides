import pytest

from fides.api.ops.api.deps import get_cache
from fides.api.ops.common_exceptions import FunctionalityNotConfigured
from fides.core.config import get_config

CONFIG = get_config()


@pytest.fixture
def mock_config():
    redis_enabled = CONFIG.redis.enabled
    CONFIG.redis.enabled = False
    yield
    CONFIG.redis.enabled = redis_enabled


@pytest.mark.usefixtures("mock_config")
def test_get_cache_not_enabled():
    with pytest.raises(FunctionalityNotConfigured):
        next(get_cache())
