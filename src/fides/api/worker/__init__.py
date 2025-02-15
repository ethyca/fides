import json
from typing import Any

from celery import VERSION_BANNER
from celery.apps.worker import Worker
from celery.signals import celeryd_after_setup
from loguru import logger

from fides.api.service.saas_request.override_implementations import *
from fides.api.tasks import (
    MESSAGING_QUEUE_NAME,
    PRIVACY_PREFERENCES_QUEUE_NAME,
    celery_app,
)


def start_worker() -> None:
    logger.info("Running Celery worker...")
    default_queue_name = celery_app.conf.get("task_default_queue", "celery")
    celery_app.worker_main(
        argv=[
            "--quiet",  # Disable Celery startup banner
            "worker",
            "--loglevel=info",
            "--concurrency=2",
            f"--queues={default_queue_name},{MESSAGING_QUEUE_NAME},{PRIVACY_PREFERENCES_QUEUE_NAME}",
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
