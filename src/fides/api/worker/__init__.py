from typing import Any, Dict, List, Optional

from celery import VERSION_BANNER
from celery.apps.worker import Worker
from celery.signals import celeryd_after_setup
from loguru import logger
from watchfiles import run_process
from watchfiles.filters import DefaultFilter

from fides.api.db.base import Base  # type: ignore
from fides.api.service.saas_request.override_implementations import *
from fides.api.tasks import (
    BULK_CONSENT_IMPORT_QUEUE_NAME,
    CONSENT_WEBHOOK_QUEUE_NAME,
    DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME,
    DISCOVERY_MONITORS_DETECTION_QUEUE_NAME,
    DISCOVERY_MONITORS_PROMOTION_QUEUE_NAME,
    DSR_QUEUE_NAME,
    MESSAGING_QUEUE_NAME,
    PRIVACY_PREFERENCES_EXPORT_JOB_QUEUE_NAME,
    PRIVACY_PREFERENCES_INGESTION_JOB_QUEUE_NAME,
    PRIVACY_PREFERENCES_QUEUE_NAME,
    celery_app,
)
from fides.config import CONFIG


class _PythonAndYamlFilter(DefaultFilter):
    """Extends DefaultFilter to only trigger on Python and YAML file changes."""

    allowed_extensions = (".py", ".yml", ".yaml")

    def __call__(self, change: Any, path: str) -> bool:
        if not super().__call__(change, path):
            return False
        return path.endswith(self.allowed_extensions)


def _parse_prefetch_map(known_queues: List[str]) -> Dict[str, int]:
    """
    Parse FIDES__CELERY__QUEUE_PREFETCH_MULTIPLIER into a {queue: int} dict.

    - The string has already been validated so all values are parseable integers.
    - Warns for any queue name not present in known_queues but still includes the entry
      (it simply will never match any active worker queue).
    - Returns an empty dict if the setting is unset.
    """
    raw = CONFIG.celery.queue_prefetch_multiplier
    if not raw:
        return {}

    result: Dict[str, int] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        queue, _, value = pair.partition("=")
        queue = queue.strip()
        if queue not in known_queues:
            logger.warning(
                f"queue_prefetch_multiplier references unknown queue {queue!r}. "
                f"Known queues: {known_queues}. This entry will have no effect."
            )
        result[queue] = int(value.strip())

    return result


def _run_celery_worker(worker_queues: str, prefetch_map: Dict[str, int]) -> None:
    """Run the Celery worker process. Extracted so it can be used as a watchfiles target."""
    active_queues = [q.strip() for q in worker_queues.split(",")]

    # Resolve prefetch multiplier — first matching queue wins
    prefetch: Optional[int] = None
    for queue in active_queues:
        if queue in prefetch_map:
            prefetch = prefetch_map[queue]
            break

    argv = [
        "--quiet",  # Disable Celery startup banner
        "worker",
        "--loglevel=info",
        f"--concurrency={CONFIG.celery.worker_concurrency}",
        f"--queues={worker_queues}",
    ]
    if prefetch is not None:
        argv.append(f"--prefetch-multiplier={prefetch}")

    without_flags = []
    if CONFIG.celery.worker_disable_heartbeat:
        without_flags.append("--without-heartbeat")
    if CONFIG.celery.worker_disable_gossip:
        without_flags.append("--without-gossip")
    if CONFIG.celery.worker_disable_mingle:
        without_flags.append("--without-mingle")
    if without_flags:
        argv += without_flags
        logger.info(
            f"Worker started with {' '.join(without_flags)} "
            f"(FIDES__CELERY__WORKER_DISABLE_HEARTBEAT={CONFIG.celery.worker_disable_heartbeat}, "
            f"FIDES__CELERY__WORKER_DISABLE_GOSSIP={CONFIG.celery.worker_disable_gossip}, "
            f"FIDES__CELERY__WORKER_DISABLE_MINGLE={CONFIG.celery.worker_disable_mingle})"
        )

    eager = CONFIG.celery.task_always_eager
    logger.info(
        f"Worker starting | queues={worker_queues} | "
        f"task_always_eager={eager} | "
        f"prefetch_multiplier={prefetch if prefetch is not None else 'default (4)'}"
    )

    celery_app.worker_main(argv=argv)


def start_worker(
    queues: Optional[str] = None,
    exclude_queues: Optional[str] = None,
    reload: bool = False,
    reload_dirs: Optional[List[str]] = None,
) -> None:
    """
    Start a Celery worker. Optionally provide a list of queues for the worker to consume,
    as a comma-separated string, or a list of queues to exclude.
    If no queues are provided, the worker will consume from all queues: the default queue,
    the messaging queue, and the privacy preferences queue.

    If reload is True, the worker will automatically restart when Python or YAML files
    change in the watched directories (similar to uvicorn --reload).
    """

    assert not queues or not exclude_queues, (
        "Cannot provide both queues and exclude_queues"
    )

    default_queue_name = celery_app.conf.get("task_default_queue", "celery")

    all_queues = [
        default_queue_name,
        MESSAGING_QUEUE_NAME,
        PRIVACY_PREFERENCES_QUEUE_NAME,
        PRIVACY_PREFERENCES_EXPORT_JOB_QUEUE_NAME,
        PRIVACY_PREFERENCES_INGESTION_JOB_QUEUE_NAME,
        DSR_QUEUE_NAME,
        CONSENT_WEBHOOK_QUEUE_NAME,
        DISCOVERY_MONITORS_DETECTION_QUEUE_NAME,
        DISCOVERY_MONITORS_CLASSIFICATION_QUEUE_NAME,
        DISCOVERY_MONITORS_PROMOTION_QUEUE_NAME,
        BULK_CONSENT_IMPORT_QUEUE_NAME,
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

    prefetch_map = _parse_prefetch_map(all_queues)

    if reload:
        watch_dirs = reload_dirs or ["src", "data"]
        logger.info(f"Hot-reload enabled, watching directories: {watch_dirs}")
        run_process(
            *watch_dirs,
            target=_run_celery_worker,
            args=(worker_queues, prefetch_map),
            watch_filter=_PythonAndYamlFilter(),
        )
    else:
        _run_celery_worker(worker_queues, prefetch_map)


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
