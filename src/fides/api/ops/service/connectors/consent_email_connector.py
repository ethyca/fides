from typing import Dict, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.connection_configuration import ConsentEmailSchema
from fides.api.ops.schemas.messaging.messaging import (
    ConsentEmailFulfillmentBodyParams,
    MessagingActionType,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors.base_connector import LimitedConnector
from fides.api.ops.service.messaging.message_dispatch_service import dispatch_message
from fides.core.config import get_config
from fides.lib.models.audit_log import AuditLog, AuditLogAction

CONFIG = get_config()


class EmailConsentConnector(LimitedConnector[None]):
    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Sends an email to the "test_email" configured, just to establish that the email workflow is working.
        """
        config = ConsentEmailSchema(**self.configuration.secrets or {})
        logger.info("Starting test connection to {}", self.configuration.key)

        db = Session.object_session(self.configuration)
        try:
            # synchronous for now since failure to send is considered a connection test failure
            dispatch_message(
                db,
                action_type=MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT,
                to_identity=Identity(email=config.test_email_address),
                service_type=CONFIG.notifications.notification_service_type,
                message_body_params=ConsentEmailFulfillmentBodyParams(
                    processor="PROCESSOR",
                    user_identity="test_user@example.com",
                    third_party_vendor_name=config.third_party_vendor_name,
                    consent_preferences=[
                        {
                            "data_use": "Example Demo Data Use: Marketing",
                            "opt_in": False,
                        }
                    ],
                ),
            )

        except MessageDispatchException as exc:
            logger.info("Email consent connector test failed with exception {}", exc)
            return ConnectionTestStatus.failed
        return ConnectionTestStatus.succeeded


def consent_email_connector_erasure_send(
    db: Session, privacy_request: PrivacyRequest, identity: Dict
) -> None:
    """
    Send emails to configured third-parties with instructions on how to erase remaining data.
    Combined all the collections on each email-based dataset into one email.
    """
    email_consent_connection_configs = db.query(ConnectionConfig).filter(
        ConnectionConfig.connection_type == ConnectionType.email_consent,
        ConnectionConfig.disabled.is_(False),
    )

    for connection_config in email_consent_connection_configs:
        secrets = ConsentEmailSchema(**connection_config.secrets or {})

        logger.info(
            "Email queued for consent request '{}' for : '{}'",
            privacy_request.id,
            connection_config.name,
        )

        # Synchronous, since failure is fatal to the privacy request
        dispatch_message(
            db,
            action_type=MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT,
            to_identity=Identity(email=secrets.recipient_email_address),
            service_type=CONFIG.notifications.notification_service_type,
            message_body_params=ConsentEmailFulfillmentBodyParams(
                processor="PROCESSOR",
                user_identity=identity.get("email") or identity.get("phone_number"),
                third_party_vendor_name=secrets.third_party_vendor_name,
                consent_preferences=privacy_request.consent_preferences,
            ),
        )

        AuditLog.create(
            db=db,
            data={
                "user_id": "system",
                "privacy_request_id": privacy_request.id,
                "action": AuditLogAction.email_sent,
                "message": f"Consent email instructions dispatched for '{connection_config.name}'",
            },
        )
