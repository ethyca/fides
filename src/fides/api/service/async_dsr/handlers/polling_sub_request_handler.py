"""Manager for polling sub-request operations and lifecycle management."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.privacy_request.request_task import (
    RequestTask,
    RequestTaskSubRequest,
)
from fides.api.models.worker_task import ExecutionLogStatus


class PollingSubRequestHandler:
    """Utility class for managing polling sub-request lifecycle and status checking."""

    @staticmethod
    def create_sub_request(
        session: Session,
        request_task: RequestTask,
        param_values_map: Dict[str, Any],
    ) -> RequestTaskSubRequest:
        """
        Create a new sub-request for tracking async polling operations.

        Args:
            session: Database session
            request_task: The parent request task
            param_values_map: Parameter values including correlation_id for polling

        Returns:
            RequestTaskSubRequest: The created sub-request
        """
        sub_request = RequestTaskSubRequest.create(
            session,
            data={
                "request_task_id": request_task.id,
                "param_values": param_values_map,
                "status": ExecutionLogStatus.pending.value,
            },
        )
        logger.info(
            f"Created sub-request {sub_request.id} for task '{request_task.id}'"
        )
        return sub_request

    @staticmethod
    def check_completion(polling_task: RequestTask) -> bool:
        """
        Check if all sub-requests for a polling task are complete.

        Args:
            polling_task: The polling task to check

        Returns:
            bool: True if all sub-requests are complete, False if still in progress
        """
        # Get all sub-requests and categorize by status
        all_sub_requests = polling_task.sub_requests
        completed_sub_requests = [
            sub_request
            for sub_request in all_sub_requests
            if sub_request.status == ExecutionLogStatus.complete.value
        ]
        failed_sub_requests = [
            sub_request
            for sub_request in all_sub_requests
            if sub_request.status == ExecutionLogStatus.error.value
        ]

        if (
            len(completed_sub_requests) == len(all_sub_requests)
            and len(all_sub_requests) > 0
        ):
            # All sub-requests completed successfully - aggregate results
            logger.info(
                f"All sub-requests completed successfully for task {polling_task.id}"
            )
            return True

        # Still polling - some sub-requests are pending
        logger.info(
            f"Polling task {polling_task.id}: {len(completed_sub_requests)}/{len(all_sub_requests)} sub-requests complete, {len(failed_sub_requests)} failed"
        )
        return False

    @staticmethod
    def check_timeout(polling_task: RequestTask, timeout_days: int) -> None:
        """
        Check if any sub-requests have exceeded the polling timeout.

        Args:
            polling_task: The polling task to check
            timeout_days: Timeout threshold in days

        Raises:
            PrivacyRequestError: If any sub-request has timed out
        """
        timeout_seconds = timeout_days * 24 * 60 * 60  # Convert days to seconds

        # Check timeout for incomplete sub-requests only
        timed_out_sub_requests = []

        for sub_request in polling_task.sub_requests:
            if sub_request.status != ExecutionLogStatus.complete.value:
                # Check if this sub-request has timed out
                if sub_request.created_at:
                    timeout_threshold = sub_request.created_at + timedelta(
                        seconds=timeout_seconds
                    )
                    current_time = datetime.now(timezone.utc)
                    if current_time > timeout_threshold:
                        timed_out_sub_requests.append(sub_request)

        if timed_out_sub_requests:
            sub_request_ids = [sr.id for sr in timed_out_sub_requests]
            raise PrivacyRequestError(
                f"Polling timeout exceeded for sub-requests {sub_request_ids} "
                f"in task {polling_task.id}. Timeout interval: {timeout_days} days"
            )
