"""Task queueing functionality."""

from loguru import logger

from fides.api.models.privacy_request import ActionType, RequestTask
from fides.api.tasks import DSR_QUEUE_NAME, celery_app
from fides.api.util.cache import cache_task_tracking_key

# Map action types to their corresponding task names
TASK_MAPPING = {
    ActionType.access: "fides.api.task.execute_request_tasks.run_access_node",
    ActionType.erasure: "fides.api.task.execute_request_tasks.run_erasure_node",
    ActionType.consent: "fides.api.task.execute_request_tasks.run_consent_node",
}


def queue_request_task(
    request_task: RequestTask, privacy_request_proceed: bool = True
) -> None:
    """Queues the RequestTask in Celery and caches the Celery Task ID"""
    task_name = TASK_MAPPING[request_task.action_type]
    celery_task = celery_app.send_task(
        task_name,
        queue=DSR_QUEUE_NAME,
        kwargs={
            "privacy_request_id": request_task.privacy_request_id,
            "privacy_request_task_id": request_task.id,
            "privacy_request_proceed": privacy_request_proceed,
        },
    )
    cache_task_tracking_key(request_task.id, celery_task.task_id)
    logger.info("Queued request task {} for execution", request_task.id)
