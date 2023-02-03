from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Organization  # type: ignore[attr-defined]
from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.connection_configuration import ConsentEmailSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets_email_consent import (
    SVORN_REQUIRED_IDENTITY,
)
from fides.api.ops.schemas.messaging.messaging import (
    ConsentEmailFulfillmentBodyParams,
    ConsentPreferencesByUser,
    MessagingActionType,
)
from fides.api.ops.schemas.privacy_request import Consent
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors.base_connector import LimitedConnector
from fides.api.ops.service.messaging.message_dispatch_service import dispatch_message
from fides.core.config import get_config
from fides.lib.models.audit_log import AuditLog, AuditLogAction

CONFIG = get_config()


def get_required_identities(email_secrets: ConsentEmailSchema) -> List[str]:
    """Return a list of identity types we need to email to the third party vendor.

    Combines identities from browser-retrieved identities and supplied identities.
    """
    advanced_settings = email_secrets.advanced_settings
    return [
        identifier.value for identifier in advanced_settings.identity_types or []
    ] + [
        identifier.value
        for identifier in advanced_settings.browser_identity_types or []
    ]


class EmailConsentConnector(LimitedConnector[None]):
    """Base Email Connector that should be shared between generic and
    vendor-specific email consent connectors"""

    @property
    def user_test_identities(self) -> Dict[str, Any]:
        return {"email": "test_email@example.com"}

    @property
    def required_identities(self) -> List[str]:
        """Returns the identity types we need to supply to the third party for this connector"""
        config = ConsentEmailSchema(**self.configuration.secrets or {})
        return get_required_identities(config)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Sends an email to the "test_email" configured, just to establish
        that the email workflow is working.
        """
        config = ConsentEmailSchema(**self.configuration.secrets or {})
        try:
            if not config.test_email_address:
                raise MessageDispatchException(
                    f"Cannot test connection. No test email defined for {self.configuration.name}"
                )

            logger.info("Starting test connection to {}", self.configuration.key)

            # synchronous for now since failure to send is considered a connection test failure
            send_consent_email(
                db=Session.object_session(self.configuration),
                subject_email=config.test_email_address,
                subject_name=config.third_party_vendor_name,
                required_identities=self.required_identities,
                user_consent_preferences=[
                    ConsentPreferencesByUser(
                        identities=self.user_test_identities,
                        consent_preferences=[
                            Consent(data_use="Email Marketing", opt_in=False),
                            Consent(data_use="Product Analytics", opt_in=True),
                        ],
                    )
                ],
                test_mode=True,
            )

        except MessageDispatchException as exc:
            logger.info("Email consent connector test failed with exception {}", exc)
            return ConnectionTestStatus.failed
        return ConnectionTestStatus.succeeded


class SovrnConsentConnector(EmailConsentConnector):
    @property
    def user_test_identities(self) -> Dict[str, Any]:
        return {SVORN_REQUIRED_IDENTITY: "test_ljt_reader_id"}


def consent_email_connector_send(
    db: Session, privacy_request: PrivacyRequest, user_identity: Dict
) -> None:
    """
    Send emails to configured processors with user consent preferences for when we can't
    update via API directly.

    """
    email_consent_connection_configs = db.query(ConnectionConfig).filter(
        ConnectionConfig.connection_type == ConnectionType.sovrn,
        ConnectionConfig.disabled.is_(False),
    )

    for connection_config in email_consent_connection_configs:
        secrets = ConsentEmailSchema(**connection_config.secrets or {})

        user_identities: Dict[str, Any] = {}
        required_identities: List[str] = get_required_identities(secrets)
        for identity_type in required_identities:
            if user_identity.get(identity_type):
                user_identities[identity_type] = user_identity.get(identity_type)

        if user_identities:
            logger.info(
                "Email dispatched for consent request '{}' for : '{}'",
                privacy_request.id,
                connection_config.name,
            )
            send_consent_email(
                db=db,
                subject_email=secrets.recipient_email_address,
                subject_name=secrets.third_party_vendor_name,
                required_identities=required_identities,
                user_consent_preferences=[
                    ConsentPreferencesByUser(
                        identities=user_identities,
                        consent_preferences=privacy_request.consent_preferences,
                    )
                ],
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
        else:
            logger.info(
                "Skipping email send for '{}': no user identities detected.",
                connection_config.name,
            )


def send_consent_email(
    db: Session,
    subject_email: str,
    subject_name: str,
    required_identities: List[str],
    user_consent_preferences: List[ConsentPreferencesByUser],
    test_mode: bool = False,
) -> None:
    """Sends a consent email"""
    org: Optional[Organization] = db.query(Organization).first()

    if not org:
        raise MessageDispatchException(
            "Cannot send an email requesting consent preference changes to third-party vendor. No organization defined."
        )

    dispatch_message(
        db,
        action_type=MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT,
        to_identity=Identity(email=subject_email),
        service_type=CONFIG.notifications.notification_service_type,
        message_body_params=ConsentEmailFulfillmentBodyParams(
            controller=org.name,
            third_party_vendor_name=subject_name,
            required_identities=required_identities,
            requested_changes=user_consent_preferences,
        ),
        subject_override=f"{'Test notification' if test_mode else 'Notification'} of users' consent preference changes from {org.name}",
    )
