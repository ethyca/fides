from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.ops.models.policy import ActionType, Rule
from fides.api.ops.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
)
from fides.api.ops.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettingsWithExtendedIdentityTypes,
    ExtendedEmailSchema,
    ExtendedIdentityTypes,
)
from fides.api.ops.schemas.messaging.messaging import (
    ConsentEmailFulfillmentBodyParams,
    ConsentPreferencesByUser,
    MessagingActionType,
)
from fides.api.ops.schemas.privacy_request import Consent
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors.base_email_connector import (
    BaseEmailConnector,
    get_email_messaging_config_service_type,
    get_org_name,
)
from fides.api.ops.service.messaging.message_dispatch_service import dispatch_message
from fides.core.config import get_config

CONFIG = get_config()

CONSENT_EMAIL_CONNECTOR_TYPES = [ConnectionType.sovrn]


class GenericConsentEmailConnector(BaseEmailConnector):
    """Generic Email Consent Connector that can be overridden for specific vendors"""

    @property
    def identities_for_test_email(self) -> Dict[str, Any]:
        return {"email": "test_email@example.com"}

    @property
    def required_identities(self) -> List[str]:
        return get_identity_types_for_connector(self.config)

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        self.config: ExtendedEmailSchema = ExtendedEmailSchema(
            **configuration.secrets or {}
        )

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Sends an email to the "test_email" configured, just to establish
        that the email workflow is working.
        """

        try:
            if not self.config.test_email_address:
                raise MessageDispatchException(
                    f"Cannot test connection. No test email defined for {self.configuration.name}"
                )

            logger.info("Starting test connection to {}", self.configuration.key)

            # synchronous since failure to send is considered a connection test failure
            send_single_consent_email(
                db=Session.object_session(self.configuration),
                subject_email=self.config.test_email_address,
                subject_name=self.config.third_party_vendor_name,
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

    def needs_email(
        self, user_identities: Dict[str, Any], privacy_request: PrivacyRequest
    ) -> bool:
        """Schedules a consent email for consent privacy requests containing consent preferences and valid user identities"""

        if not privacy_request.consent_preferences:
            return False

        consent_rules: List[Rule] = privacy_request.policy.get_rules_for_action(
            action_type=ActionType.consent
        )
        return bool(
            consent_rules
            and filter_user_identities_for_connector(self.config, user_identities)
        )

    def batch_email_send(self, privacy_requests: Query) -> None:
        skipped_privacy_requests: List[str] = []
        batched_consent_preferences: List[ConsentPreferencesByUser] = []

        for privacy_request in privacy_requests:
            user_identities: Dict[str, Any] = privacy_request.get_cached_identity_data()
            filtered_user_identities: Dict[
                str, Any
            ] = filter_user_identities_for_connector(self.config, user_identities)
            if filtered_user_identities and privacy_request.consent_preferences:
                batched_consent_preferences.append(
                    ConsentPreferencesByUser(
                        identities=filtered_user_identities,
                        consent_preferences=privacy_request.consent_preferences,
                    )
                )
            else:
                skipped_privacy_requests.append(privacy_request.id)

        if not batched_consent_preferences:
            logger.info(
                "Skipping consent email send for connector: '{}'. "
                "No corresponding user identities found for pending privacy requests.",
                self.configuration.name,
            )
            return

        logger.info(
            "Sending batched consent email for connector {}...",
            self.configuration.name,
        )

        db = Session.object_session(self.configuration)

        try:
            send_single_consent_email(
                db=db,
                subject_email=self.config.recipient_email_address,
                subject_name=self.config.third_party_vendor_name,
                required_identities=self.required_identities,
                user_consent_preferences=batched_consent_preferences,
                test_mode=False,
            )
        except MessageDispatchException as exc:
            logger.info("Consent email failed with exception {}", exc)
            raise

        for privacy_request in privacy_requests:
            if privacy_request.id not in skipped_privacy_requests:
                ExecutionLog.create(
                    db=db,
                    data={
                        "connection_key": self.configuration.key,
                        "dataset_name": self.configuration.name,
                        "privacy_request_id": privacy_request.id,
                        "action_type": ActionType.consent,
                        "status": ExecutionLogStatus.complete,
                        "message": f"Consent email instructions dispatched for '{self.configuration.name}'",
                    },
                )

        if skipped_privacy_requests:
            logger.info(
                "Skipping email send for the following privacy request IDs: "
                "{} on connector '{}': no matching identities detected.",
                skipped_privacy_requests,
                self.configuration.name,
            )


def get_identity_types_for_connector(
    email_secrets: ExtendedEmailSchema,
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
    secrets: ExtendedEmailSchema, user_identities: Dict[str, Any]
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

    org_name = get_org_name(db)

    dispatch_message(
        db=db,
        action_type=MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT,
        to_identity=Identity(email=subject_email),
        service_type=get_email_messaging_config_service_type(db=db),
        message_body_params=ConsentEmailFulfillmentBodyParams(
            controller=org_name,
            third_party_vendor_name=subject_name,
            required_identities=required_identities,
            requested_changes=user_consent_preferences,
        ),
        subject_override=f"{'Test notification' if test_mode else 'Notification'} "
        f"of users' consent preference changes from {org_name}",
    )
