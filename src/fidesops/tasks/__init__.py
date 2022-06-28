from celery import Celery
from celery.utils.log import get_task_logger

from fidesops.core.config import config

logger = get_task_logger(__name__)


def _create_celery() -> Celery:
    """
    Returns a configured version of the Celery application
    """
    logger.info("Creating Celery app...")
    app = Celery(__name__)
    app.conf.update(broker_url=config.execution.CELERY_BROKER_URL)
    app.conf.update(result_backend=config.execution.CELERY_RESULT_BACKEND)
    logger.info("Autodiscovering tasks...")
    app.autodiscover_tasks(
        [
            "fidesops.tasks",
            "fidesops.tasks.scheduled",
            "fidesops.service.privacy_request",
        ]
    )
    return app


celery_app = _create_celery()


def start_worker() -> None:
    logger.info("Running Celery worker...")
    celery_app.worker_main(argv=["worker", "--loglevel=info"])


if __name__ == "__main__":
    start_worker()
