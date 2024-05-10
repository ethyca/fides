from typing import Any, ContextManager, Dict, List, Optional

from celery import Celery, Task
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.db.session import get_db_engine, get_db_session
from fides.api.util.logger import create_handler_dicts
from fides.api.util.logger import setup as setup_logging
from fides.config import CONFIG, FidesConfig

MESSAGING_QUEUE_NAME = "fidesops.messaging"


class DatabaseTask(Task):  # pylint: disable=W0223
    _task_engine = None
    _sessionmaker = None

    def get_new_session(self) -> ContextManager[Session]:
        """
        Creates a new Session to be used for each task invocation.

        The new Sessions will reuse a shared `Engine` and `sessionmaker`
        across invocations, so as to reuse db connection resources.
        """
        # only one engine will be instantiated in a given task scope, i.e
        # once per celery process.
        if self._task_engine is None:
            _task_engine = get_db_engine(
                config=CONFIG,
                pool_size=CONFIG.database.task_engine_pool_size,
                max_overflow=CONFIG.database.task_engine_max_overflow,
            )

        # same for the sessionmaker
        if self._sessionmaker is None:
            self._sessionmaker = get_db_session(config=CONFIG, engine=_task_engine)

        # but a new session is instantiated each time the method is invoked
        # to prevent session overlap when requests are executing concurrently
        # when in task_always_eager mode (i.e. without proper workers)
        return self._sessionmaker()


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

    app.autodiscover_tasks(
        [
            "fides.api.tasks",
            "fides.api.tasks.scheduled",
            "fides.api.service.privacy_request",
            "fides.api.service.privacy_request.request_runner_service",
        ]
    )

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
