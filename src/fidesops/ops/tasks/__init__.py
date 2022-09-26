from typing import Any, ContextManager, Dict, MutableMapping

from celery import Celery, Task
from celery.utils.log import get_task_logger
from fideslib.core.config import load_toml
from fideslib.db.session import get_db_session
from sqlalchemy.orm import Session

from fidesops.ops.core.config import config

logger = get_task_logger(__name__)

EMAIL_QUEUE_NAME = "fidesops.email"


class DatabaseTask(Task):  # pylint: disable=W0223
    _session = None

    @property
    def session(self) -> ContextManager[Session]:
        """Creates Session once per process"""
        if self._session is None:
            SessionLocal = get_db_session(config)
            self._session = SessionLocal()

        return self._session


def _create_celery(config_path: str = config.execution.celery_config_path) -> Celery:
    """
    Returns a configured version of the Celery application
    """
    logger.info("Creating Celery app...")
    app = Celery(__name__)

    celery_config: Dict[str, Any] = {
        # Defaults for the celery config
        "broker_url": config.redis.connection_url,
        "result_backend": config.redis.connection_url,
        # Fidesops requires this to route emails to separate queues
        "task_create_missing_queues": True,
    }

    try:
        celery_config_overrides: MutableMapping[str, Any] = load_toml([config_path])
    except FileNotFoundError as e:
        logger.warning("celery.toml could not be loaded: %s", e)
    else:
        celery_config.update(celery_config_overrides)

    app.conf.update(celery_config)

    logger.info("Autodiscovering tasks...")
    app.autodiscover_tasks(
        [
            "fidesops.ops.tasks",
            "fidesops.ops.tasks.scheduled",
            "fidesops.ops.service.privacy_request",
        ]
    )
    return app


celery_app = _create_celery()


def start_worker() -> None:
    logger.info("Running Celery worker...")
    default_queue_name = celery_app.conf.get("task_default_queue", "celery")
    celery_app.worker_main(
        argv=[
            "worker",
            "--loglevel=info",
            "--concurrency=2",
            f"--queues={default_queue_name},{EMAIL_QUEUE_NAME}",
        ]
    )


if __name__ == "__main__":
    start_worker()
