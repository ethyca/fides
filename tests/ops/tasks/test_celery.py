import os
from unittest.mock import patch

import pytest

from fides.api.tasks import _create_celery, celery_app
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


@patch.dict(
    os.environ,
    {
        "FIDES__CELERY__WORKER_PREFETCH_MULTIPLIER": "4",
        "FIDES__CELERY__TASK_ACKS_LATE": "true",
        "FIDES__CELERY__WORKER_MAX_TASKS_PER_CHILD": "1000",
        "FIDES__CELERY__TASK_ALWAYS_EAGER": "false",  # Override known field
    },
    clear=False,
)
def test_celery_arbitrary_env_vars() -> None:
    """Test that arbitrary Celery configuration can be set via FIDES__CELERY__* env vars."""
    # Clear the config cache to force reload with new env vars
    get_config.cache_clear()

    config = get_config()

    # Create celery app with the config
    celery_app = _create_celery(config=config)

    # Known field that was overridden via env var
    assert celery_app.conf["task_always_eager"] is False

    # Arbitrary Celery settings that aren't explicitly defined in CelerySettings
    assert celery_app.conf["worker_prefetch_multiplier"] == 4
    assert celery_app.conf["task_acks_late"] is True
    assert celery_app.conf["worker_max_tasks_per_child"] == 1000

    # Clear cache again for other tests
    get_config.cache_clear()


def test_celery_cluster_mode_uses_cluster_urls() -> None:
    """When redis.cluster_enabled is True, broker and result_backend use redis+cluster://."""
    config = get_config()
    cluster_url = "redis+cluster://:redispassword@127.0.0.1:6380/0"
    with patch.object(config.redis, "cluster_enabled", True), patch.object(
        config.redis, "get_cluster_connection_url", return_value=cluster_url
    ):
        celery_app = _create_celery(config=config)
        assert celery_app.conf["broker_url"] == cluster_url
        assert celery_app.conf["result_backend"] == cluster_url


def test_celery_cluster_mode_respects_broker_backend_override() -> None:
    """When cluster_enabled but broker_url/result_backend are set, overrides are used."""
    config = get_config()
    config.celery.broker_url = "redis://broker:6379/0"
    config.celery.result_backend = "redis://backend:6379/1"
    cluster_url = "redis+cluster://127.0.0.1:6380/0"
    with patch.object(config.redis, "cluster_enabled", True), patch.object(
        config.redis, "get_cluster_connection_url", return_value=cluster_url
    ):
        app = _create_celery(config=config)
        assert app.conf["broker_url"] == "redis://broker:6379/0"
        assert app.conf["result_backend"] == "redis://backend:6379/1"


def test_celery_cluster_broker_connect() -> None:
    """
    Integration: when Redis cluster is enabled, the default Celery app can connect
    to the broker (redis+cluster). Skip if cluster is not running.
    Run with cluster: FIDES__REDIS__CLUSTER_ENABLED=true FIDES__REDIS__HOST=127.0.0.1
    FIDES__REDIS__PORT=6380 FIDES__REDIS__PASSWORD=redispassword (and Procfile.redis-cluster).
    """
    if not CONFIG.redis.cluster_enabled:
        pytest.skip("Redis cluster not enabled")
    conn = celery_app.connection()
    try:
        conn.connect()
        conn.release()
    except Exception as e:
        pytest.skip(
            f"Redis cluster broker not reachable (start Procfile.redis-cluster or "
            f"docker compose redis cluster): {e}"
        )


@patch.dict(
    os.environ,
    {
        "FIDES__CELERY__BROKER_URL": "Redis://myhost:6379/0",
        "FIDES__CELERY__RESULT_BACKEND": "redis://SecretPassword@host:6379/1",
        "FIDES__CELERY__TASK_ALWAYS_EAGER": "True",  # Capital T
        "FIDES__CELERY__TASK_ACKS_LATE": "False",  # Capital F
        "FIDES__CELERY__CUSTOM_STRING": "MixedCaseValue",
    },
    clear=False,
)
def test_celery_env_vars_preserve_case_sensitivity() -> None:
    """
    Test that case-sensitive values like URLs and passwords are preserved,
    while boolean strings are still parsed correctly regardless of case.
    """
    # Clear the config cache to force reload with new env vars
    get_config.cache_clear()

    config = get_config()
    celery_app = _create_celery(config=config)

    # URLs with uppercase characters should be preserved
    assert celery_app.conf["broker_url"] == "Redis://myhost:6379/0"
    assert celery_app.conf["result_backend"] == "redis://SecretPassword@host:6379/1"

    # Boolean strings should be parsed regardless of case
    assert celery_app.conf["task_always_eager"] is True
    assert celery_app.conf["task_acks_late"] is False

    # Custom case-sensitive strings should be preserved
    assert celery_app.conf["custom_string"] == "MixedCaseValue"

    # Clear cache again for other tests
    get_config.cache_clear()
