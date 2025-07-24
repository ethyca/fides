from typing import Any, List, Optional

from celery import VERSION_BANNER
from celery.apps.worker import Worker
from celery.signals import celeryd_after_setup
from loguru import logger

from fides.api.db.base import Base  # type: ignore
from fides.api.service.saas_request.override_implementations import *
from fides.api.tasks import (
    DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME,
    DISCOVERY_MONITORS_DETECTION_QUEUE_NAME,
    DISCOVERY_MONITORS_PROMOTION_QUEUE_NAME,
    DSR_QUEUE_NAME,
    MESSAGING_QUEUE_NAME,
    PRIVACY_PREFERENCES_QUEUE_NAME,
    celery_app,
)


def start_worker(
    queues: Optional[str] = None, exclude_queues: Optional[str] = None
) -> None:
    """
    Start a Celery worker. Optionally provide a list of queues for the worker to consume,
    as a comma-separated string, or a list of queues to exclude.
    If no queues are provided, the worker will consume from all queues: the default queue,
    the messaging queue, and the privacy preferences queue.
    """

    assert (
        not queues or not exclude_queues
    ), "Cannot provide both queues and exclude_queues"

    default_queue_name = celery_app.conf.get("task_default_queue", "celery")

    all_queues = [
        default_queue_name,
        MESSAGING_QUEUE_NAME,
        PRIVACY_PREFERENCES_QUEUE_NAME,
        DSR_QUEUE_NAME,
        DISCOVERY_MONITORS_DETECTION_QUEUE_NAME,
        DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME,
        DISCOVERY_MONITORS_PROMOTION_QUEUE_NAME,
    ]

    # Fall back to all queues if neither queues nor exclude_queues are provided.
    worker_queues = ",".join(all_queues)

    if queues:
        validate_queues(queues, all_queues)
        # If queues are provided, use them.
        worker_queues = queues

    # If excluded queues are provided, remove them from the list of all queues.
    if exclude_queues:
        validate_queues(exclude_queues, all_queues)
        excluded_queues = exclude_queues.split(",")
        worker_queues = ",".join(
            [queue for queue in all_queues if queue not in excluded_queues]
        )

    logger.info(f"Running Celery worker for queues: {worker_queues}")

    celery_app.worker_main(
        argv=[
            "--quiet",  # Disable Celery startup banner
            "worker",
            "--loglevel=info",
            "--concurrency=2",
            f"--queues={worker_queues}",
        ]
    )


def validate_queues(queues_string: str, known_queues: List[str]) -> None:
    """
    Validate that the provided queues string is a comma-separated list of known queues.
    """
    queues = queues_string.split(",")
    unknown_queues = [queue for queue in queues if queue not in known_queues]
    if unknown_queues:
        raise ValueError(f"Unknown queues: {unknown_queues}")


@celeryd_after_setup.connect
def log_celery_setup(sender: str, instance: Worker, **kwargs: Any) -> None:
    """In lieu of the Celery banner, print the connection details"""
    app = instance.app
    celery_details = {
        "hostname": instance.hostname,
        "version": VERSION_BANNER,
        "app": "{0}:{1:#x}".format(app.main or "__main__", id(app)),
        "transport": app.connection().as_uri(),
        "results": app.backend.as_uri(),
        "concurrency": str(instance.concurrency),
        "queues": "|".join(str(queue) for queue in app.amqp.queues.keys()),
    }

    logger.bind(celery_details=celery_details).info("Celery connection setup complete")


if __name__ == "__main__":  # pragma: no cover
    start_worker()
