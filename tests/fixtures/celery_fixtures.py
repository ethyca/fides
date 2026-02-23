import pytest
from loguru import logger
from toml import load as load_toml

from fides.api.tasks import celery_healthcheck
from fides.config import get_config

CONFIG = get_config()


@pytest.fixture(scope="session")
def integration_config():
    yield load_toml("tests/fixtures/integration_test_config.toml")


@pytest.fixture(scope="session")
def celery_config(request):
    """
    Configure celery for testing.

    Uses a unique healthcheck port per xdist worker to prevent port conflicts
    when running tests in parallel.
    """
    # Calculate unique port based on xdist worker_id
    # This works at session scope by accessing request.config
    if hasattr(request.config, "workerinput"):
        # In a worker process (e.g., 'gw0', 'gw1', 'gw2')
        worker_id = request.config.workerinput["workerid"]
        worker_num = int(worker_id.replace("gw", ""))
        healthcheck_port = 9000 + worker_num + 1
    else:
        # In the master process (or not using xdist)
        healthcheck_port = 9000

    return {
        "task_always_eager": False,
        "healthcheck_port": healthcheck_port,
    }


@pytest.fixture(scope="session")
def celery_enable_logging():
    """Turns on celery output logs."""
    return True


@pytest.fixture(scope="session")
def celery_session_app(celery_session_app):
    celery_healthcheck.register(celery_session_app)
    return celery_session_app


# This is here because the test suite occasionally fails to teardown the
# Celery worker if it takes too long to terminate the worker thread. This
# will prevent that and, instead, log a warning
@pytest.fixture(scope="session")
def celery_session_worker(
    request,
    celery_session_app,
    celery_includes,
    celery_class_tasks,
    celery_worker_pool,
    celery_worker_parameters,
):
    from celery.contrib.testing import worker

    for module in celery_includes:
        celery_session_app.loader.import_task_module(module)
    for class_task in celery_class_tasks:
        celery_session_app.register_task(class_task)

    try:
        logger.info("Starting safe celery session worker...")
        with worker.start_worker(
            celery_session_app,
            pool=celery_worker_pool,
            shutdown_timeout=2.0,
            **celery_worker_parameters,
        ) as w:
            try:
                yield w
                logger.info("Done with celery worker, trying to dispose of it..")
            except RuntimeError:
                logger.warning("Failed to dispose of the celery worker.")
    except RuntimeError as re:
        logger.warning("Failed to stop the celery worker: " + str(re))


@pytest.fixture(autouse=True, scope="session")
def celery_use_virtual_worker(celery_session_worker):
    """
    This is a catch-all fixture that forces all of our
    tests to use a virtual celery worker if a registered
    task is executed within the scope of the test.
    """
    yield celery_session_worker


@pytest.fixture(scope="session")
def run_privacy_request_task(celery_session_app):
    """
    This fixture is the version of the run_privacy_request task that is
    registered to the `celery_app` fixture which uses the virtualised `celery_worker`
    """
    yield celery_session_app.tasks[
        "fides.service.privacy_request.request_runner_service.run_privacy_request"
    ]


@pytest.fixture(scope="session")
def analytics_opt_out():
    """Disable sending analytics when running tests."""
    original_value = CONFIG.user.analytics_opt_out
    CONFIG.user.analytics_opt_out = True
    yield
    CONFIG.user.analytics_opt_out = original_value
