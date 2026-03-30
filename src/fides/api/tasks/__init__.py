from typing import Any, ContextManager, Dict, List, Optional

import celery_redis_cluster_backend  # type: ignore[import-untyped]  # noqa: F401 - registers redis+cluster/rediss+cluster backends
from celery import Celery, Task
from celery.signals import before_task_publish, task_postrun, task_prerun
from celery.signals import setup_logging as celery_setup_logging
from loguru import logger
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from fides.api.db.session import get_db_engine, get_db_session
from fides.api.request_context import get_request_id, set_request_id
from fides.api.tasks import celery_healthcheck
from fides.api.util.logger import setup as setup_logging
from fides.config import CONFIG, FidesConfig

MESSAGING_QUEUE_NAME = "fidesops.messaging"
PRIVACY_PREFERENCES_QUEUE_NAME = "fides.privacy_preferences"  # This queue is used in Fidesplus for saving privacy preferences and notices served
PRIVACY_PREFERENCES_EXPORT_JOB_QUEUE_NAME = "fides.privacy_request_exports"
PRIVACY_PREFERENCES_INGESTION_JOB_QUEUE_NAME = "fides.privacy_request_ingestion"
DSR_QUEUE_NAME = "fides.dsr"  # This queue is used for running data subject requests
CONSENT_WEBHOOK_QUEUE_NAME = "fidesplus.consent_webhooks"  # This queue is used for processing consent webhooks from 3rd-party APIs
DISCOVERY_MONITORS_DETECTION_QUEUE_NAME = "fidesplus.discovery_monitors_detection"  # This queue is used for running discovery monitors detection tasks
DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME = "fidesplus.discovery_monitors_classification"  # This queue is used for running discovery monitors classification tasks
DISCOVERY_MONITORS_PROMOTION_QUEUE_NAME = "fidesplus.discovery_monitors_promotion"  # This queue is used for running discovery monitors promotion tasks
BULK_CONSENT_IMPORT_QUEUE_NAME = "fidesplus.bulk_consent_import"  # This queue is used for bulk importing pre-verified consent records


NEW_SESSION_RETRIES = 5

autodiscover_task_locations: List[str] = [
    "fides.api.tasks",
    "fides.api.tasks.scheduled",
    "fides.api.service.privacy_request",
    "fides.api.service.privacy_request.request_runner_service",
]


def log_retry_attempt(retry_state: RetryCallState) -> None:
    """Log database connection retry attempts."""

    logger.warning(
        "Database connection attempt {} failed. Retrying in {} seconds...",
        retry_state.attempt_number,
        retry_state.next_action.sleep,  # type: ignore[union-attr]
    )


class DatabaseTask(Task):  # pylint: disable=W0223
    _task_engine = None
    _sessionmaker = None

    # This retry will attempt to connect 5 times with an exponential backoff (2, 4, 8, 16 seconds between each attempt).
    # The original error will be re-raised if the retries are successful. All attempts are shown in the logs.
    @retry(
        stop=stop_after_attempt(NEW_SESSION_RETRIES),
        wait=wait_exponential(multiplier=1, min=1),
        retry=retry_if_exception_type(OperationalError),
        reraise=True,
        before_sleep=log_retry_attempt,
    )
    def get_new_session(self) -> ContextManager[Session]:
        """
        Creates a new Session to be used for each task invocation.

        The new Sessions will reuse a shared `Engine` and `sessionmaker`
        across invocations, so as to reuse db connection resources.
        """
        # only one engine will be instantiated in a given task scope, i.e
        # once per celery process.
        if self._task_engine is None:
            self._task_engine = get_db_engine(
                config=CONFIG,
                pool_size=CONFIG.database.task_engine_pool_size,
                max_overflow=CONFIG.database.task_engine_max_overflow,
                keepalives_idle=CONFIG.database.task_engine_keepalives_idle,
                keepalives_interval=CONFIG.database.task_engine_keepalives_interval,
                keepalives_count=CONFIG.database.task_engine_keepalives_count,
                pool_pre_ping=CONFIG.database.task_engine_pool_pre_ping,
            )

        # same for the sessionmaker
        if self._sessionmaker is None:
            self._sessionmaker = get_db_session(config=CONFIG, engine=self._task_engine)

        # but a new session is instantiated each time the method is invoked
        # to prevent session overlap when requests are executing concurrently
        # when in task_always_eager mode (i.e. without proper workers)
        new_session = self._sessionmaker()
        return new_session


def _create_celery(config: FidesConfig = CONFIG) -> Celery:
    """
    Returns a configured version of the Celery application
    """
    setup_logging(config)
    logger.bind(api_config=CONFIG.logging.json()).debug(
        "Logger configuration options in use"
    )

    app = Celery(__name__)
    celery_healthcheck.register(app)  # type: ignore

    # celery-redis-cluster registers under 'celery.backends' but Celery looks for
    # 'celery.result_backends'; patch loader so redis+cluster:// uses RedisClusterBackend.
    if config.redis.cluster_enabled:
        from importlib.metadata import entry_points

        cluster_backends = {
            ep.name: ep.value for ep in entry_points(group="celery.backends")
        }
        if cluster_backends:
            app.loader.override_backends = (
                getattr(app.loader, "override_backends", {}) | cluster_backends
            )

    # Broker and result backend. When redis.cluster_enabled is True we use redis+cluster://
    # (via celery-redis-cluster) unless overridden. Otherwise use redis.connection_url.
    if config.celery.broker_url is not None:
        broker_url = config.celery.broker_url
    elif config.redis.cluster_enabled:
        broker_url = config.redis.get_cluster_connection_url()
    else:
        connection_url = config.redis.connection_url
        if connection_url is None:
            raise ValueError(
                "Redis connection_url is required when cluster is disabled"
            )
        broker_url = connection_url

    if config.celery.result_backend is not None:
        result_backend = config.celery.result_backend
    elif config.redis.cluster_enabled:
        result_backend = config.redis.get_cluster_connection_url()
    else:
        connection_url = config.redis.connection_url
        if connection_url is None:
            raise ValueError(
                "Redis connection_url is required when cluster is disabled"
            )
        result_backend = connection_url

    celery_config: Dict[str, Any] = {
        "broker_url": broker_url,
        "result_backend": result_backend,
        "event_queue_prefix": "fides_worker",
        "task_always_eager": True,
        # Ops requires this to route emails to separate queues
        "task_create_missing_queues": True,
        "task_default_queue": "fides",
        "worker_prefetch_multiplier": 1,
        "healthcheck_port": config.celery.healthcheck_port,
        "healthcheck_ping_timeout": config.celery.healthcheck_ping_timeout,
    }

    celery_config.update(config.celery)
    # Preserve broker/backend in case config.celery overwrote them with None
    celery_config["broker_url"] = broker_url
    celery_config["result_backend"] = result_backend

    app.conf.update(celery_config)

    app.autodiscover_tasks(autodiscover_task_locations)

    return app


celery_app = _create_celery(CONFIG)


@celery_setup_logging.connect
def configure_celery_logging(**kwargs: Any) -> None:
    """
    Prevent Celery from configuring logging on worker startup.

    By connecting to the setup_logging signal and doing nothing, we prevent Celery
    from overriding our Loguru logging configuration. Our logging setup in _create_celery
    has already configured logging with InterceptHandler to capture all stdlib logs.
    """


@before_task_publish.connect
def _propagate_request_id(headers: Dict[str, Any], **kwargs: Any) -> None:
    """Attach the current request_id to outgoing Celery task headers.

    This runs in the *publisher* process (API server) so the ContextVar
    holds the request_id set by ``LogRequestMiddleware``.
    """
    request_id = get_request_id()
    if request_id is not None:
        headers["request_id"] = request_id


@task_prerun.connect
def _restore_request_id(task: Task, **kwargs: Any) -> None:
    """Restore request_id from the task headers into the worker's ContextVar.

    This runs in the *worker* process before the task body executes, so all
    logs emitted by the task are tagged with the originating request_id.
    """
    request_id = getattr(task.request, "request_id", None)
    if request_id is not None:
        set_request_id(request_id)


@task_postrun.connect
def _clear_request_id(**kwargs: Any) -> None:
    """Clear request_id after task completion.

    Celery workers reuse processes for multiple tasks. Without this cleanup,
    a request_id from Task A would leak into Task B if Task B was dispatched
    without a request_id header.
    """
    set_request_id(None)


def get_worker_ids() -> List[Optional[str]]:
    """
    Returns a list of the connected healthy worker UUIDs.
    """
    try:
        connected_workers = [
            key for key, _ in celery_app.control.inspect().ping().items()
        ]
    except Exception as exception:
        logger.critical(exception)
        connected_workers = []
    return connected_workers
