# pylint: disable=protected-access

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

import fides.api.api.deps
from fides.api.api.deps import get_api_session, get_cache
from fides.api.common_exceptions import RedisNotConfigured
from fides.config import CONFIG


@pytest.fixture
def mock_config():
    redis_enabled = CONFIG.redis.enabled
    CONFIG.redis.enabled = False
    yield
    CONFIG.redis.enabled = redis_enabled


@pytest.fixture
def mock_config_changed_db_engine_settings():
    pool_size = CONFIG.database.api_engine_pool_size
    CONFIG.database.api_engine_pool_size = pool_size + 5
    max_overflow = CONFIG.database.api_engine_max_overflow
    CONFIG.database.api_engine_max_overflow = max_overflow + 5
    yield
    CONFIG.database.api_engine_pool_size = pool_size
    CONFIG.database.api_engine_max_overflow = max_overflow


@pytest.mark.usefixtures("mock_config")
def test_get_cache_not_enabled():
    with pytest.raises(RedisNotConfigured):
        next(get_cache())


@pytest.mark.parametrize(
    "config_fixture", [None, "mock_config_changed_db_engine_settings"]
)
def test_get_api_session(config_fixture, request):
    if config_fixture is not None:
        request.getfixturevalue(
            config_fixture
        )  # used to invoke config fixture if provided
    fides.api.api.deps._engine = None
    pool_size = CONFIG.database.api_engine_pool_size
    max_overflow = CONFIG.database.api_engine_max_overflow
    session: Session = get_api_session()
    engine: Engine = session.get_bind()
    pool: QueuePool = engine.pool
    assert pool.size() == pool_size
    assert pool._max_overflow == max_overflow
