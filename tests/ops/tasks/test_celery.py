from fides.api.ops.tasks import _create_celery
from fides.core.config import get_config

CONFIG = get_config()


def test_create_task(celery_session_app, celery_session_worker):
    @celery_session_app.task
    def multiply(x, y):
        return x * y

    # Force `celery_app` to register our new task
    # See: https://github.com/celery/celery/issues/3642#issuecomment-369057682
    celery_session_worker.reload()
    assert multiply.run(4, 4) == 16
    assert multiply.delay(4, 4).get(timeout=10) == 16


def test_celery_default_config() -> None:
    celery_app = _create_celery()
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
