from fides.api.tasks import _create_celery
from fides.config import CONFIG, CelerySettings, get_config


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
    assert isinstance(config.celery, CelerySettings)
    assert config.celery.task_always_eager
    assert config.celery.event_queue_prefix == "fides_worker"
    assert config.celery.task_default_queue == "fides"

    celery_app = _create_celery(config)
    assert celery_app.conf["broker_url"] == CONFIG.redis.connection_url
    assert celery_app.conf["result_backend"] == CONFIG.redis.connection_url
    assert celery_app.conf["event_queue_prefix"] == "fides_worker"
    assert celery_app.conf["task_default_queue"] == "fides"
    assert celery_app.conf["task_always_eager"] is True


def test_celery_config_override() -> None:
    config = get_config()

    config.celery.event_queue_prefix = "overridden_fides_worker"
    config.celery.task_default_queue = "overridden_fides"

    celery_app = _create_celery(config=config)
    assert celery_app.conf["event_queue_prefix"] == "overridden_fides_worker"
    assert celery_app.conf["task_default_queue"] == "overridden_fides"
