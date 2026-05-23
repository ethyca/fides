"""Activity for finalizing a completed privacy request."""

from __future__ import annotations

from temporalio import activity


@activity.defn
async def finalize_privacy_request(privacy_request_id: str) -> str:
    """Mark the privacy request as complete, send notifications, create audit log.

    Returns the final status string.
    """
    from datetime import datetime

    from sqlalchemy.orm import selectinload

    from fides.api.models.audit_log import AuditLog, AuditLogAction
    from fides.api.models.policy import Policy
    from fides.api.models.privacy_request import PrivacyRequest
    from fides.api.schemas.policy import ActionType
    from fides.api.schemas.privacy_request import PrivacyRequestStatus
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = (
            session.query(PrivacyRequest)
            .options(
                selectinload(PrivacyRequest.policy).selectinload(Policy.rules),
            )
            .filter(PrivacyRequest.id == privacy_request_id)
            .first()
        )
        if not privacy_request:
            raise ValueError(f"Privacy request {privacy_request_id} not found")

        if privacy_request.status == PrivacyRequestStatus.error:
            return privacy_request.status.value

        policy = privacy_request.policy

        AuditLog.create(
            db=session,
            data={
                "user_id": "system",
                "privacy_request_id": privacy_request.id,
                "action": AuditLogAction.finished,
                "message": "",
            },
        )

        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.finished_processing_at = datetime.utcnow()
        privacy_request.save(session)
        session.commit()

        identity_data = {
            key: value["value"] if isinstance(value, dict) else value
            for key, value in privacy_request.get_cached_identity_data().items()
        }

        from fides.api.schemas.messaging.messaging import MessagingActionType
        from fides.api.service.messaging.message_dispatch_service import (
            message_send_enabled,
        )
        from fides.config.config_proxy import ConfigProxy

        config_proxy = ConfigProxy(session)
        notification_enabled = (
            config_proxy.notifications.send_request_completion_notification
        )
        if message_send_enabled(
            session,
            privacy_request.property_id,
            MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS,
            bool(notification_enabled),
        ):
            if policy.get_rules_for_action(
                ActionType.access
            ) or policy.get_rules_for_action(ActionType.erasure):
                from fides.api.service.privacy_request.request_runner_service import (
                    initiate_privacy_request_completion_email,
                )

                access_result_urls = (privacy_request.access_result_urls or {}).get(
                    "access_result_urls", []
                )

                initiate_privacy_request_completion_email(
                    session,
                    policy,
                    access_result_urls,
                    identity_data,
                    privacy_request.property_id,
                    privacy_request.id,
                )

        return privacy_request.status.value


@activity.defn
async def prepare_erasure_tasks(privacy_request_id: str) -> bool:
    """Update erasure RequestTasks with access data from completed access tasks.

    Called between access and erasure phases. Returns True if erasure tasks exist.
    """
    from fides.api.models.privacy_request import PrivacyRequest
    from fides.api.task.create_request_tasks import (
        update_erasure_tasks_with_access_data,
    )
    from fides.common.session_management import get_autoclose_db_session

    with get_autoclose_db_session() as session:
        privacy_request = PrivacyRequest.get(db=session, object_id=privacy_request_id)
        if not privacy_request:
            raise ValueError(f"Privacy request {privacy_request_id} not found")

        update_erasure_tasks_with_access_data(session, privacy_request)
        return privacy_request.erasure_tasks.count() > 0
