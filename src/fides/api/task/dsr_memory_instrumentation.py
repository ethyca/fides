"""
Enhanced DSR task execution with integrated memory tracking.

This module provides wrapper functions and utilities to instrument existing DSR tasks
with memory tracking without significantly modifying their core logic.
"""

from typing import Any, List

from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.task.graph_task import GraphTask
from fides.api.util.collection_util import Row
from fides.api.util.dsr_memory_tracker import memory_tracking_context


def run_graph_task_with_memory_tracking(
    session: Session,
    request_task: RequestTask,
    privacy_request: PrivacyRequest,
    graph_task: GraphTask,
    upstream_access_data: List[List[Row]],
    action_type: str,
) -> Any:
    """
    Run a graph task (access/erasure/consent) with memory tracking.

    Args:
        session: Database session
        request_task: The RequestTask being executed
        privacy_request: The PrivacyRequest
        graph_task: The GraphTask to execute
        upstream_access_data: Upstream data for access tasks
        action_type: "access", "erasure", or "consent"

    Returns:
        The result of the graph task execution
    """
    # Get the Celery task ID from the current context if available
    task_id = "unknown"
    try:
        from celery import current_task

        if current_task:
            task_id = current_task.request.id
    except Exception:
        pass

    with memory_tracking_context(
        task_name=f"run_{action_type}_node",
        task_id=task_id,
        privacy_request_id=privacy_request.id,
        privacy_request_task_id=request_task.id,
        collection_address=request_task.collection_address,
        session=session,
    ) as metrics:
        # Execute the appropriate action
        if action_type == "access":
            result = graph_task.access_request(*upstream_access_data)
        elif action_type == "erasure":
            result = graph_task.erasure_request()
        elif action_type == "consent":
            # For consent, access_data is a single dict
            access_data_dict = upstream_access_data[0] if upstream_access_data else {}
            result = graph_task.consent_request(access_data_dict)
        else:
            raise ValueError(f"Unknown action_type: {action_type}")

        # Try to capture metrics from the task results
        try:
            # Access requests store data in request_task
            if action_type == "access":
                access_data = request_task.get_access_data() or []
                metrics.rows = len(access_data)
                # Estimate size from stored data
                from fides.api.util.dsr_memory_tracker import MemoryTracker

                tracker = MemoryTracker()
                metrics.payload_size_bytes = tracker.estimate_payload_size(access_data)

            # Erasure requests have a rows_masked count
            elif action_type == "erasure":
                metrics.rows = request_task.rows_masked or 0

        except Exception:
            # Don't fail the task if metrics collection fails
            pass

        return result
