from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.ctl.sql_models import Organization  # type: ignore[attr-defined]
from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_email_consent import (
    AdvancedSettingsWithExtendedIdentityTypes,
    ExtendedConsentEmailSchema,
    ExtendedIdentityTypes,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_sovrn import (
    SOVRN_REQUIRED_IDENTITY,
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

CONFIG = get_config()

CONSENT_EMAIL_CONNECTOR_TYPES = [ConnectionType.sovrn]


class GenericEmailConsentConnector(LimitedConnector[None]):
    """Generic Email Consent Connector that can be overridden for specific vendors"""

    @property
    def identities_for_test_email(self) -> Dict[str, Any]:
        """The mock user identities that are sent in the test
        email to ensure the connector is working"""
        return {"email": "test_email@example.com"}

    @property
    def required_identities(self) -> List[str]:
        """Returns the identity types we need to supply to the third party for this connector"""
        config = ExtendedConsentEmailSchema(**self.configuration.secrets or {})
        return get_identity_types_for_connector(config)

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Sends an email to the "test_email" configured, just to establish
        that the email workflow is working.
        """
        config = ExtendedConsentEmailSchema(**self.configuration.secrets or {})
        try:
            if not config.test_email_address:
                raise MessageDispatchException(
                    f"Cannot test connection. No test email defined for {self.configuration.name}"
                )

            logger.info("Starting test connection to {}", self.configuration.key)

            # synchronous since failure to send is considered a connection test failure
            send_single_consent_email(
                db=Session.object_session(self.configuration),
                subject_email=config.test_email_address,
                subject_name=config.third_party_vendor_name,
                required_identities=self.required_identities,
                user_consent_preferences=[
                    ConsentPreferencesByUser(
                        identities=self.identities_for_test_email,
                        consent_preferences=[
                            Consent(data_use="advertising", opt_in=False),
                            Consent(data_use="improve", opt_in=True),
                        ],
                    )
                ],
                test_mode=True,
            )

        except MessageDispatchException as exc:
            logger.info("Email consent connector test failed with exception {}", exc)
            return ConnectionTestStatus.failed
        return ConnectionTestStatus.succeeded


class SovrnConsentConnector(GenericEmailConsentConnector):
    """SovrnConsentConnector - only need to override the details for the test email."""

    @property
    def identities_for_test_email(self) -> Dict[str, Any]:
        return {SOVRN_REQUIRED_IDENTITY: "test_ljt_reader_id"}


def get_consent_email_connection_configs(db: Session) -> Query:
    """Return enabled consent-type email connection configs."""
    return db.query(ConnectionConfig).filter(
        ConnectionConfig.connection_type.in_(CONSENT_EMAIL_CONNECTOR_TYPES),
        ConnectionConfig.disabled.is_(False),
        ConnectionConfig.access == AccessLevel.write,
    )


def get_identity_types_for_connector(
    email_secrets: ExtendedConsentEmailSchema,
) -> List[str]:
    """Return a list of identity types we need to email to the third party vendor."""
    advanced_settings: AdvancedSettingsWithExtendedIdentityTypes = (
        email_secrets.advanced_settings
    )
    identity_types: ExtendedIdentityTypes = advanced_settings.identity_types
    flattened_list: List[str] = identity_types.cookie_ids

    if identity_types.email:
        flattened_list.append("email")
    if identity_types.phone_number:
        flattened_list.append("phone_number")

    return flattened_list


def filter_user_identities_for_connector(
    secrets: ExtendedConsentEmailSchema, user_identities: Dict[str, Any]
) -> Dict[str, Any]:
    """Filter identities to just those specified for a given connector"""
    required_identities: List[str] = get_identity_types_for_connector(secrets)
    return {
        identity_type: user_identities.get(identity_type)
        for identity_type in required_identities
        if user_identities.get(identity_type)
    }


def send_single_consent_email(
    db: Session,
    subject_email: str,
    subject_name: str,
    required_identities: List[str],
    user_consent_preferences: List[ConsentPreferencesByUser],
    test_mode: bool = False,
) -> None:
    """Sends a single consent email"""
    org: Optional[Organization] = (
        db.query(Organization).order_by(Organization.created_at.desc()).first()
    )

    if not org or not org.name:
        raise MessageDispatchException(
            "Cannot send an email requesting consent preference changes to third-party vendor. "
            "No organization name found."
        )

    dispatch_message(
        db=db,
        action_type=MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT,
        to_identity=Identity(email=subject_email),
        service_type=CONFIG.notifications.notification_service_type,
        message_body_params=ConsentEmailFulfillmentBodyParams(
            controller=org.name,
            third_party_vendor_name=subject_name,
            required_identities=required_identities,
            requested_changes=user_consent_preferences,
        ),
        subject_override=f"{'Test notification' if test_mode else 'Notification'} "
        f"of users' consent preference changes from {org.name}",
    )
