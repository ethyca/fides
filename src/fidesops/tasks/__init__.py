from typing import Any, Dict, MutableMapping

from celery import Celery
from celery.utils.log import get_task_logger
from fideslib.core.config import load_toml

from fidesops.core.config import config
from fidesops.util.logger import NotPii

logger = get_task_logger(__name__)


def _create_celery(config_path: str = config.execution.CELERY_CONFIG_PATH) -> Celery:
    """
    Returns a configured version of the Celery application
    """
    logger.info("Creating Celery app...")
    app = Celery(__name__)

    celery_config: Dict[str, Any] = {
        # Defaults for the celery config
        "broker_url": config.redis.CONNECTION_URL,
        "result_backend": config.redis.CONNECTION_URL,
    }

    try:
        celery_config_overrides: MutableMapping[str, Any] = load_toml([config_path])
    except FileNotFoundError as e:
        logger.warning("celery.toml could not be loaded: %s", NotPii(e))
    else:
        celery_config.update(celery_config_overrides)

    app.conf.update(celery_config)

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
