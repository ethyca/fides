from __future__ import annotations

from typing import Any, Optional

from loguru import logger


class CeleryDSREngine:
    """DSR execution engine backed by Celery task queues."""

    def dispatch_privacy_request(
        self,
        privacy_request_id: str,
        from_webhook_id: Optional[str] = None,
        from_step: Optional[str] = None,
    ) -> Optional[str]:
        from fides.api.service.privacy_request.request_runner_service import (
            run_privacy_request,
        )
        from fides.api.tasks import DSR_QUEUE_NAME
        from fides.api.util.cache import cache_task_tracking_key

        task = run_privacy_request.apply_async(
            queue=DSR_QUEUE_NAME,
            kwargs={
                "privacy_request_id": privacy_request_id,
                "from_webhook_id": from_webhook_id,
                "from_step": from_step,
            },
        )
        cache_task_tracking_key(privacy_request_id, task.task_id)
        return task.task_id

    def dispatch_request_task(
        self,
        request_task_id: str,
        privacy_request_id: str,
        action_type: str,
        privacy_request_proceed: bool = True,
    ) -> None:
        from fides.api.task.execute_request_tasks import queue_request_task

        logger.info(
            "Dispatching {} task {} via Celery",
            action_type,
            request_task_id,
        )
        # queue_request_task expects a RequestTask ORM object,
        # but callers in the Celery path already call it directly.
        # This method exists for protocol compliance.
        raise NotImplementedError(
            "CeleryDSREngine.dispatch_request_task is not used directly. "
            "Celery tasks call queue_request_task with the ORM object."
        )

    def signal_task_complete(
        self,
        privacy_request_id: str,
        collection_address: str,
        data: Optional[dict[str, Any]] = None,
    ) -> None:
        # In the Celery path, signals are handled by the callback endpoint
        # directly re-queuing the request task. No engine-level signal needed.
        raise NotImplementedError(
            "CeleryDSREngine.signal_task_complete is not used. "
            "Celery callback endpoint queues tasks directly."
        )
