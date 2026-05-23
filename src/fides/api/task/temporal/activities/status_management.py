"""Activities for managing privacy request status and execution state."""

from __future__ import annotations

from temporalio import activity


@activity.defn
async def run_pre_webhooks(
    privacy_request_id: str, from_webhook_id: str | None
) -> bool:
    """Execute pre-processing webhooks. Returns True if execution should proceed."""
    from fides.api.models.pre_approval_webhook import PreApprovalWebhook
    from fides.api.models.privacy_request import PrivacyRequest
    from fides.api.service.privacy_request.request_runner_service import (
        run_webhooks_and_report_status,
    )
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = PrivacyRequest.get(db=session, object_id=privacy_request_id)
        if not privacy_request:
            raise ValueError(f"Privacy request {privacy_request_id} not found")

        from fides.api.models.policy import PolicyPreWebhook

        proceed = run_webhooks_and_report_status(
            db=session,
            privacy_request=privacy_request,
            webhook_cls=PolicyPreWebhook,
            after_webhook_id=from_webhook_id,
        )
        return proceed


@activity.defn
async def run_post_webhooks(privacy_request_id: str) -> bool:
    """Execute post-processing webhooks. Returns True if execution should proceed."""
    from fides.api.models.privacy_request import PrivacyRequest
    from fides.api.service.privacy_request.request_runner_service import (
        run_webhooks_and_report_status,
    )
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = PrivacyRequest.get(db=session, object_id=privacy_request_id)
        if not privacy_request:
            raise ValueError(f"Privacy request {privacy_request_id} not found")

        from fides.api.models.policy import PolicyPostWebhook

        proceed = run_webhooks_and_report_status(
            db=session,
            privacy_request=privacy_request,
            webhook_cls=PolicyPostWebhook,
        )
        return proceed


@activity.defn
async def update_privacy_request_status(
    privacy_request_id: str,
    status: str,
) -> None:
    """Update the privacy request status."""
    from fides.api.models.privacy_request import PrivacyRequest
    from fides.api.schemas.privacy_request import PrivacyRequestStatus
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = PrivacyRequest.get(db=session, object_id=privacy_request_id)
        if not privacy_request:
            raise ValueError(f"Privacy request {privacy_request_id} not found")

        privacy_request.status = PrivacyRequestStatus(status)
        privacy_request.save(session)


@activity.defn
async def mark_request_task_failed(
    request_task_id: str,
    error_message: str,
) -> None:
    """Mark a request task and all its descendants as failed."""
    from fides.api.models.privacy_request import RequestTask
    from fides.api.task.graph_task import mark_current_and_downstream_nodes_as_failed
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        request_task = RequestTask.get(session, request_task_id)
        if request_task:
            mark_current_and_downstream_nodes_as_failed(
                request_task, session, Exception(error_message)
            )
