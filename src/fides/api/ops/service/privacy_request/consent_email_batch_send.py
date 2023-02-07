from typing import Any, Dict, List

from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Query

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.policy import CurrentStep
from fides.api.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.ops.schemas.connection_configuration import ConsentEmailSchema
from fides.api.ops.schemas.messaging.messaging import ConsentPreferencesByUser
from fides.api.ops.service.connectors.consent_email_connector import (
    get_consent_email_connection_configs,
    get_identity_types_for_connector,
    get_user_identities_for_connector,
    send_single_consent_email,
)
from fides.api.ops.service.privacy_request.request_runner_service import (
    queue_privacy_request,
)
from fides.api.ops.tasks import DatabaseTask, celery_app
from fides.lib.models.audit_log import AuditLog, AuditLogAction


class BatchedConsentEmailData(BaseModel):
    """Schema to store the details for the batched consent emails: one per connector"""

    connection_name: str
    required_identities: List[str]
    connection_secrets: ConsentEmailSchema
    user_consent_preferences: List[ConsentPreferencesByUser] = []
    skipped_privacy_requests: List[str] = []


@celery_app.task(base=DatabaseTask, bind=True)
def send_consent_email_batch(self: DatabaseTask) -> None:
    """Sends consent emails to each relevant connector with
    applicable user details batched together."""

    logger.info("Starting batch consent email send...")
    with self.session as session:
        privacy_requests: Query = session.query(PrivacyRequest).filter(
            PrivacyRequest.status == PrivacyRequestStatus.awaiting_consent_email_send
        )

        if not privacy_requests:
            logger.info(
                "Skipping batch consent email send.  No privacy requests with status: {}",
                PrivacyRequestStatus.awaiting_consent_email_send.value,
            )
            return

        consent_email_connection_configs: Query = get_consent_email_connection_configs(
            session
        )
        batched_email_data: List[BatchedConsentEmailData] = []
        # First, stage some data for each of the third parties for which we'll send emails
        for connection_config in consent_email_connection_configs:
            secrets: ConsentEmailSchema = ConsentEmailSchema(
                **connection_config.secrets or {}
            )
            batched_email_data.append(
                BatchedConsentEmailData(
                    connection_secrets=secrets,
                    connection_name=connection_config.name,
                    required_identities=get_identity_types_for_connector(secrets),
                )
            )

        # Loop through each privacy request to see if we have user identities for each pending email
        for privacy_request in privacy_requests:
            user_identities: Dict[str, Any] = privacy_request.get_cached_identity_data()

            for pending_email in batched_email_data:
                filtered_user_identities: Dict[
                    str, Any
                ] = get_user_identities_for_connector(
                    pending_email.connection_secrets, user_identities
                )

                # TODO REMOVE THIS - FOR TESTING ONLY
                filtered_user_identities["ljt_readerID"] = "12345"

                if filtered_user_identities:
                    pending_email.user_consent_preferences.append(
                        ConsentPreferencesByUser(
                            identities=filtered_user_identities,
                            consent_preferences=privacy_request.consent_preferences,
                        )
                    )
                else:
                    pending_email.skipped_privacy_requests.append(privacy_request.id)

        # Send one email per connector
        for pending_email in batched_email_data:
            if not pending_email.user_consent_preferences:
                logger.info(
                    "Skipping consent email send for connector: '{}'. No corresponding user identities found for pending privacy requests.",
                    pending_email.connection_name,
                )
                continue

            try:
                send_single_consent_email(
                    db=session,
                    subject_email=pending_email.connection_secrets.recipient_email_address,
                    subject_name=pending_email.connection_secrets.third_party_vendor_name,
                    required_identities=pending_email.required_identities,
                    user_consent_preferences=pending_email.user_consent_preferences,
                    test_mode=False,
                )
            except MessageDispatchException as exc:
                logger.error(
                    "Consent email send for connector: {} failed with exception {}",
                    pending_email.connection_name,
                    exc,
                )
                raise exc

            # Add Audit Logs for each privacy request
            for privacy_request in privacy_requests:
                if privacy_request.id not in pending_email.skipped_privacy_requests:
                    AuditLog.create(
                        db=session,
                        data={
                            "user_id": "system",
                            "privacy_request_id": privacy_request.id,
                            "action": AuditLogAction.email_sent,
                            "message": f"Consent email instructions dispatched for '{pending_email.connection_name}'",
                        },
                    )
            if pending_email.skipped_privacy_requests:
                logger.info(
                    "Skipping email send for the following privacy request ids '{}': no matching identities detected.",
                    pending_email.skipped_privacy_requests,
                )

    # Requeue privacy requests to wrap up processing
    for privacy_request in privacy_requests:
        queue_privacy_request(
            privacy_request_id=privacy_request.id,
            from_step=CurrentStep.post_webhooks.value,
        )
