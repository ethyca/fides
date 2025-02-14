import json
from typing import Any, Optional

from celery import VERSION_BANNER
from celery.apps.worker import Worker
from celery.signals import celeryd_after_setup
from loguru import logger

from fides.api.service.saas_request.override_implementations import *
from fides.api.tasks import (
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
    ]
    # If queues are provided, use them. Otherwise, use all queues.
    worker_queues = queues or ",".join(all_queues)

    # If excluded queues are provided, remove them from the list of all queues.
    if exclude_queues:
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
