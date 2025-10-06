from typing import Any, ContextManager, Dict, List, Optional

from celery import Celery, Task
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
from fides.api.util.logger import setup as setup_logging
from fides.config import CONFIG, FidesConfig

MESSAGING_QUEUE_NAME = "fidesops.messaging"
PRIVACY_PREFERENCES_QUEUE_NAME = "fides.privacy_preferences"  # This queue is used in Fidesplus for saving privacy preferences and notices served
DSR_QUEUE_NAME = "fides.dsr"  # This queue is used for running data subject requests
CONSENT_WEBHOOK_QUEUE_NAME = "fidesplus.consent_webhooks"  # This queue is used for processing consent webhooks from 3rd-party APIs
DISCOVERY_MONITORS_DETECTION_QUEUE_NAME = "fidesplus.discovery_monitors_detection"  # This queue is used for running discovery monitors detection tasks
DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME = "fidesplus.discovery_monitors_classification"  # This queue is used for running discovery monitors classification tasks
DISCOVERY_MONITORS_PROMOTION_QUEUE_NAME = "fidesplus.discovery_monitors_promotion"  # This queue is used for running discovery monitors promotion tasks


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

    celery_config: Dict[str, Any] = {
        # Defaults for the celery config
        "broker_url": config.redis.connection_url,
        "result_backend": config.redis.connection_url,
        "event_queue_prefix": "fides_worker",
        "task_always_eager": True,
        # Ops requires this to route emails to separate queues
        "task_create_missing_queues": True,
        "task_default_queue": "fides",
    }

    celery_config.update(config.celery)

    app.conf.update(celery_config)

    app.autodiscover_tasks(autodiscover_task_locations)

    return app


celery_app = _create_celery(CONFIG)


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
