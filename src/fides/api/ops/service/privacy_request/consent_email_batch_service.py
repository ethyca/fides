from enum import Enum
from typing import Any, Dict, List

from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Query, Session

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.policy import CurrentStep
from fides.api.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.ops.schemas.connection_configuration.connection_secrets_email_consent import (
    ExtendedConsentEmailSchema,
)
from fides.api.ops.schemas.messaging.messaging import ConsentPreferencesByUser
from fides.api.ops.service.connectors.consent_email_connector import (
    filter_user_identities_for_connector,
    get_consent_email_connection_configs,
    get_identity_types_for_connector,
    send_single_consent_email,
)
from fides.api.ops.service.privacy_request.request_runner_service import (
    queue_privacy_request,
)
from fides.api.ops.tasks import DatabaseTask, celery_app
from fides.api.ops.tasks.scheduled.scheduler import scheduler
from fides.core.config import get_config
from fides.lib.models.audit_log import AuditLog, AuditLogAction

CONFIG = get_config()
BATCH_CONSENT_EMAIL_SEND = "batch_consent_email_send"


class BatchedUserConsentData(BaseModel):
    """Schema to store the batched user consent preferences for each connector"""

    connection_name: str
    required_identities: List[str]
    connection_secrets: ExtendedConsentEmailSchema
    batched_user_consent_preferences: List[ConsentPreferencesByUser] = []
    skipped_privacy_requests: List[str] = []


class ConsentEmailExitState(Enum):
    """A schema to describe where the consent email send process exited.
    For logging and testing"""

    no_applicable_privacy_requests = "no_applicable_privacy_requests"
    no_applicable_connectors = "no_applicable_connectors"
    missing_required_data = "missing_required_data"
    email_send_failed = "email_send_failed"
    complete = "complete"


def stage_resource_per_connector(
    consent_email_connection_configs: Query,
) -> List[BatchedUserConsentData]:
    """
    Build a starting resource for each consent email connector that we'll use to gather all the
    relevant user identities and consent preferences to send in a single email.
    """
    batched_email_data: List[BatchedUserConsentData] = []

    for connection_config in consent_email_connection_configs:
        secrets: ExtendedConsentEmailSchema = ExtendedConsentEmailSchema(
            **connection_config.secrets or {}
        )
        batched_email_data.append(
            BatchedUserConsentData(
                connection_secrets=secrets,
                connection_name=connection_config.name,
                required_identities=get_identity_types_for_connector(secrets),
            )
        )
    return batched_email_data


def add_batched_user_preferences_to_emails(
    privacy_requests: Query, batched_user_data: List[BatchedUserConsentData]
) -> None:
    """
    Collect user identities and consent preferences across privacy requests for each applicable connector

    ! Edits batched_user_data in place
    """
    for privacy_request in privacy_requests:
        user_identities: Dict[str, Any] = privacy_request.get_cached_identity_data()

        for pending_email in batched_user_data:
            filtered_user_identities: Dict[
                str, Any
            ] = filter_user_identities_for_connector(
                pending_email.connection_secrets, user_identities
            )

            if filtered_user_identities and privacy_request.consent_preferences:
                pending_email.batched_user_consent_preferences.append(
                    ConsentPreferencesByUser(
                        identities=filtered_user_identities,
                        consent_preferences=privacy_request.consent_preferences,
                    )
                )
            else:
                pending_email.skipped_privacy_requests.append(privacy_request.id)


def send_prepared_emails(
    db: Session,
    batched_user_data: List[BatchedUserConsentData],
    privacy_requests: Query,
) -> int:
    """Send a single consent email for each connector using the prepared data in batched_user_data

    Also add audit logs to each relevant privacy request.
    """
    emails_sent: int = 0
    for pending_email in batched_user_data:
        if not pending_email.batched_user_consent_preferences:
            logger.info(
                "Skipping consent email send for connector: '{}'. "
                "No corresponding user identities found for pending privacy requests.",
                pending_email.connection_name,
            )
            continue

        logger.info(
            "Sending batched consent email for connector {}...",
            pending_email.connection_name,
        )
        send_single_consent_email(
            db=db,
            subject_email=pending_email.connection_secrets.recipient_email_address,
            subject_name=pending_email.connection_secrets.third_party_vendor_name,
            required_identities=pending_email.required_identities,
            user_consent_preferences=pending_email.batched_user_consent_preferences,
            test_mode=False,
        )

        for privacy_request in privacy_requests:
            if privacy_request.id not in pending_email.skipped_privacy_requests:
                AuditLog.create(
                    db=db,
                    data={
                        "user_id": "system",
                        "privacy_request_id": privacy_request.id,
                        "action": AuditLogAction.email_sent,
                        "message": f"Consent email instructions dispatched for '{pending_email.connection_name}'",
                    },
                )

        if pending_email.skipped_privacy_requests:
            logger.info(
                "Skipping email send for the following privacy request ids: "
                "{} on connector '{}': no matching identities detected.",
                pending_email.skipped_privacy_requests,
                pending_email.connection_name,
            )

        emails_sent += 1
    return emails_sent


@celery_app.task(base=DatabaseTask, bind=True)
def send_consent_email_batch(self: DatabaseTask) -> ConsentEmailExitState:
    """Sends consent emails for each relevant connector with
    applicable user details batched together."""

    logger.info("Starting batched consent email send...")
    with self.get_new_session() as session:

        privacy_requests: Query = session.query(PrivacyRequest).filter(
            PrivacyRequest.status == PrivacyRequestStatus.awaiting_consent_email_send
        )
        if not privacy_requests.first():
            logger.info(
                "Skipping batch consent email send with status: {}",
                ConsentEmailExitState.no_applicable_privacy_requests.value,
            )
            return ConsentEmailExitState.no_applicable_privacy_requests

        conn_configs: Query = get_consent_email_connection_configs(session)
        if not conn_configs.first():
            requeue_privacy_requests_after_consent_email_send(privacy_requests, session)
            logger.info(
                "Skipping batch consent email send with status: {}",
                ConsentEmailExitState.no_applicable_connectors.value,
            )
            return ConsentEmailExitState.no_applicable_connectors

        batched_user_data: List[BatchedUserConsentData] = stage_resource_per_connector(
            conn_configs
        )
        add_batched_user_preferences_to_emails(privacy_requests, batched_user_data)

        if not any(
            pending_email.batched_user_consent_preferences
            for pending_email in batched_user_data
        ):
            requeue_privacy_requests_after_consent_email_send(privacy_requests, session)
            logger.info(
                "Skipping batch consent email send with status: {}",
                ConsentEmailExitState.missing_required_data.value,
            )
            return ConsentEmailExitState.missing_required_data

        try:
            send_prepared_emails(session, batched_user_data, privacy_requests)
        except MessageDispatchException as exc:
            logger.error(
                "Consent email send for connector failed with exception: '{}'",
                exc,
            )
            return ConsentEmailExitState.email_send_failed

    requeue_privacy_requests_after_consent_email_send(privacy_requests, session)
    return ConsentEmailExitState.complete


def requeue_privacy_requests_after_consent_email_send(
    privacy_requests: Query, db: Session
) -> None:
    """After batch consent email send, requeue privacy requests from the post webhooks step
    to wrap up processing and transition to a "complete" state.

    Also cache on the privacy request itself that it is paused at the post-webhooks state,
    in case something happens in re-queueing.
    """
    logger.info("Batched consent email send complete.")
    logger.info("Queuing privacy requests from 'post_webhooks' step.")
    for privacy_request in privacy_requests:
        privacy_request.cache_paused_collection_details(
            step=CurrentStep.post_webhooks,
            collection=None,
            action_needed=None,
        )
        privacy_request.status = PrivacyRequestStatus.paused
        privacy_request.save(db=db)

        queue_privacy_request(
            privacy_request_id=privacy_request.id,
            from_step=CurrentStep.post_webhooks.value,
        )


def initiate_scheduled_batch_consent_email_send() -> None:
    """Initiates scheduler to add weekly batch consent email send"""

    if CONFIG.is_test_mode:
        return

    logger.info("Initiating scheduler for batch consent email send")
    scheduler.add_job(
        func=send_consent_email_batch,
        kwargs={},
        id=BATCH_CONSENT_EMAIL_SEND,
        coalesce=False,
        replace_existing=True,
        trigger="cron",
        minute="0",
        hour="12",
        day_of_week="mon",
        timezone="US/Eastern",
    )
