# pylint: disable=protected-access
import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

from fides.api.tasks import DatabaseTask, _create_celery
from fides.core.config import CONFIG, get_config


@pytest.fixture
def mock_config_changed_db_engine_settings():
    pool_size = CONFIG.database.task_engine_pool_size
    CONFIG.database.task_engine_pool_size = pool_size + 5
    max_overflow = CONFIG.database.task_engine_max_overflow
    CONFIG.database.task_engine_max_overflow = max_overflow + 5
    yield
    CONFIG.database.task_engine_pool_size = pool_size
    CONFIG.database.task_engine_max_overflow = max_overflow


def test_create_task(celery_session_app, celery_session_worker):
    @celery_session_app.task
    def multiply(x, y):
        return x * y

    # Force `celery_app` to register our new task
    # See: https://github.com/celery/celery/issues/3642#issuecomment-369057682
    celery_session_worker.reload()
    assert multiply.run(4, 4) == 16
    assert multiply.delay(4, 4).get(timeout=10) == 16


def test_task_config_is_test_mode(celery_session_app, celery_session_worker):
    @celery_session_app.task
    def get_virtualised_worker_config():
        return get_config().test_mode

    # Force `celery_app` to register our new task
    # See: https://github.com/celery/celery/issues/3642#issuecomment-369057682
    celery_session_worker.reload()
    sync_is_test_mode = get_virtualised_worker_config.run()
    async_is_test_mode = get_virtualised_worker_config.delay().get(timeout=10)

    assert sync_is_test_mode
    assert async_is_test_mode


def test_celery_default_config() -> None:
    config = get_config()
    celery_app = _create_celery(config)
    assert celery_app.conf["broker_url"] == CONFIG.redis.connection_url
    assert celery_app.conf["result_backend"] == CONFIG.redis.connection_url
    assert celery_app.conf["event_queue_prefix"] == "fides_worker"
    assert celery_app.conf["task_default_queue"] == "fides"


def test_celery_config_override() -> None:
    config = get_config()

    config.celery["event_queue_prefix"] = "overridden_fides_worker"
    config.celery["task_default_queue"] = "overridden_fides"

    celery_app = _create_celery(config=config)
    assert celery_app.conf["event_queue_prefix"] == "overridden_fides_worker"
    assert celery_app.conf["task_default_queue"] == "overridden_fides"


@pytest.mark.parametrize(
    "config_fixture", [None, "mock_config_changed_db_engine_settings"]
)
def test_get_task_session(config_fixture, request):
    if config_fixture is not None:
        request.getfixturevalue(
            config_fixture
        )  # used to invoke config fixture if provided
    pool_size = CONFIG.database.task_engine_pool_size
    max_overflow = CONFIG.database.task_engine_max_overflow
    t = DatabaseTask()
    session: Session = t.get_new_session()
    engine: Engine = session.get_bind()
    pool: QueuePool = engine.pool
    assert pool.size() == pool_size
    assert pool._max_overflow == max_overflow
