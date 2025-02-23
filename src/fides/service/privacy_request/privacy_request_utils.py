from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import CurrentStep
from fides.api.schemas.privacy_request import PrivacyRequestResponse, PrivacyRequestStatus
from fides.api.tasks import celery_app
from fides.config import CONFIG

DSR_QUEUE_NAME = "fides.dsr"

def _process_privacy_request_restart(
    privacy_request: PrivacyRequest,
    failed_step: Optional[CurrentStep],
    db: Session,
) -> PrivacyRequestResponse:
    """If failed_step is provided, restart the DSR within that step. Otherwise,
    restart the privacy request from the beginning."""
    if failed_step:
        logger.info(
            "Restarting failed privacy request '{}' from '{}'",
            privacy_request.id,
            failed_step,
        )
    else:
        logger.info(
            "Restarting failed privacy request '{}' from the beginning",
            privacy_request.id,
        )

    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db=db)
    queue_privacy_request(
        privacy_request_id=privacy_request.id,
        from_step=failed_step.value if failed_step else None,
    )

    return privacy_request  # type: ignore[return-value]

def queue_privacy_request(
    privacy_request_id: str,
    from_webhook_id: Optional[str] = None,
    from_step: Optional[str] = None,
) -> str:
    """Queue a privacy request for processing"""
    logger.info("Queueing privacy request from step {}", from_step)

    from fides.api.service.privacy_request.request_runner_service import (
        run_privacy_request,
    )

    task = run_privacy_request.apply_async(
        queue=DSR_QUEUE_NAME,
        kwargs={
            "privacy_request_id": privacy_request_id,
            "from_webhook_id": from_webhook_id,
            "from_step": from_step,
        },
    )
    from fides.api.util.cache import cache_task_tracking_key
    cache_task_tracking_key(privacy_request_id, task.task_id)

    return task.task_id
