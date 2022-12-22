from typing import Any, ContextManager, Dict, List, MutableMapping, Optional, Union

from celery import Celery, Task
from loguru import logger
from sqlalchemy.orm import Session
from toml import load as load_toml

from fides.core.config import FidesConfig, get_config
from fides.lib.db.session import get_db_session

CONFIG = get_config()
MESSAGING_QUEUE_NAME = "fidesops.messaging"


class DatabaseTask(Task):  # pylint: disable=W0223
    _session = None

    @property
    def session(self) -> ContextManager[Session]:
        """Creates Session once per process"""
        if self._session is None:
            SessionLocal = get_db_session(CONFIG)
            self._session = SessionLocal()

        return self._session


def _create_celery(config: FidesConfig = get_config()) -> Celery:
    """
    Returns a configured version of the Celery application
    """
    logger.info("Creating Celery app...")
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

    logger.info("Autodiscovering tasks...")
    app.autodiscover_tasks(
        [
            "fides.api.ops.tasks",
            "fides.api.ops.tasks.scheduled",
            "fides.api.ops.service.privacy_request",
            "fides.api.ops.service.privacy_request.request_runner_service",
        ]
    )
    return app


celery_app = _create_celery()


def get_worker_ids() -> List[Optional[str]]:
    """
    Returns a list of the connected heahtly worker UUIDs.
    """
    try:
        connected_workers = [
            key for key, _ in celery_app.control.inspect().ping().items()
        ]
    except Exception as exception:
        logger.critical(exception)
        connected_workers = []
    return connected_workers


def start_worker() -> None:
    logger.info("Running Celery worker...")
    default_queue_name = celery_app.conf.get("task_default_queue", "celery")
    celery_app.worker_main(
        argv=[
            "worker",
            "--loglevel=info",
            "--concurrency=2",
            f"--queues={default_queue_name},{MESSAGING_QUEUE_NAME}",
        ]
    )


if __name__ == "__main__":
    start_worker()
