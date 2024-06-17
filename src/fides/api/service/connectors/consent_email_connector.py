from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    UserConsentPreference,
)
from fides.api.models.privacy_preference import PrivacyPreferenceHistory
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
)
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettingsWithExtendedIdentityTypes,
    ExtendedEmailSchema,
    ExtendedIdentityTypes,
)
from fides.api.schemas.messaging.messaging import (
    ConsentEmailFulfillmentBodyParams,
    ConsentPreferencesByUser,
    MessagingActionType,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_notice import PrivacyNoticeHistorySchema
from fides.api.schemas.privacy_preference import MinimalPrivacyPreferenceHistorySchema
from fides.api.schemas.privacy_request import Consent
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors.base_email_connector import (
    BaseEmailConnector,
    get_email_messaging_config_service_type,
    get_org_name,
)
from fides.api.service.messaging.message_dispatch_service import dispatch_message
from fides.api.util.consent_util import (
    add_complete_system_status_for_consent_reporting,
    add_errored_system_status_for_consent_reporting,
    cache_initial_status_and_identities_for_consent_reporting,
    filter_privacy_preferences_for_propagation,
)
from fides.config import get_config

CONFIG = get_config()

CONSENT_EMAIL_CONNECTOR_TYPES = [
    ConnectionType.generic_consent_email,
    ConnectionType.sovrn,
]


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
                        consent_preferences=[  # TODO slated for deprecation
                            Consent(data_use="marketing.advertising", opt_in=False),
                            Consent(data_use="functional", opt_in=True),
                        ],
                        privacy_preferences=[
                            MinimalPrivacyPreferenceHistorySchema(
                                preference=UserConsentPreference.opt_in,
                                privacy_notice_history=PrivacyNoticeHistorySchema(
                                    name="Targeted Advertising",
                                    notice_key="targeted_advertising",
                                    id="test_1",
                                    translation_id="12345",
                                    consent_mechanism=ConsentMechanism.opt_in,
                                    data_uses=[
                                        "marketing.advertising.first_party.targeted"
                                    ],
                                    enforcement_level=EnforcementLevel.system_wide,
                                    version=1.0,
                                ),
                            ),
                            MinimalPrivacyPreferenceHistorySchema(
                                preference=UserConsentPreference.opt_out,
                                privacy_notice_history=PrivacyNoticeHistorySchema(
                                    name="Analytics",
                                    notice_key="analytics",
                                    id="test_2",
                                    translation_id="67890",
                                    consent_mechanism=ConsentMechanism.opt_out,
                                    data_uses=["functional.service.improve"],
                                    enforcement_level=EnforcementLevel.system_wide,
                                    version=1.0,
                                ),
                            ),
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
        """Schedules a consent email for consent privacy requests containing consent preferences (old workflow) / privacy preferences
        (new workflow) and valid user identities
        """
        if not privacy_request.policy.get_rules_for_action(
            action_type=ActionType.consent
        ):
            return False

        old_workflow_consent_preferences: Optional[Any] = (
            privacy_request.consent_preferences
        )
        new_workflow_consent_preferences: List[PrivacyPreferenceHistory] = (
            filter_privacy_preferences_for_propagation(
                self.configuration.system,
                privacy_request.privacy_preferences,  # type: ignore[attr-defined]
            )
        )
        if not (old_workflow_consent_preferences or new_workflow_consent_preferences):
            return False

        if not filter_user_identities_for_connector(self.config, user_identities):
            return False

        return True

    def add_skipped_log(self, db: Session, privacy_request: PrivacyRequest) -> None:
        """Add skipped log for the connector to the privacy request and also cache this skipped status
        on *all* privacy preferences as no privacy preferences are relevant for this connector.
        """
        ExecutionLog.create(
            db=db,
            data={
                "connection_key": self.configuration.key,
                "dataset_name": self.configuration.name,
                "collection_name": self.configuration.name,
                "privacy_request_id": privacy_request.id,
                "action_type": ActionType.consent,
                "status": ExecutionLogStatus.skipped,
                "message": f"Consent email skipped for '{self.configuration.name}'",
            },
        )
        for pref in privacy_request.privacy_preferences:  # type: ignore[attr-defined]
            pref.cache_system_status(
                db, self.configuration.system_key, ExecutionLogStatus.skipped
            )

    def add_errored_log(self, db: Session, privacy_request: PrivacyRequest) -> None:
        """Add errored log for the connector to the privacy request and also cache this error
        on the subset of relevant privacy request preferences"""
        ExecutionLog.create(
            db=db,
            data={
                "connection_key": self.configuration.key,
                "dataset_name": self.configuration.name,
                "collection_name": self.configuration.name,
                "privacy_request_id": privacy_request.id,
                "action_type": ActionType.consent,
                "status": ExecutionLogStatus.error,
                "message": f"Consent email send error for '{self.configuration.name}'",
            },
        )
        add_errored_system_status_for_consent_reporting(
            db, privacy_request, self.configuration
        )

    def batch_email_send(self, privacy_requests: Query) -> None:
        db = Session.object_session(self.configuration)

        skipped_privacy_requests: List[str] = []
        batched_consent_preferences: List[ConsentPreferencesByUser] = []

        for privacy_request in privacy_requests:
            user_identities: Dict[str, Any] = privacy_request.get_cached_identity_data()
            filtered_user_identities: Dict[str, Any] = (
                filter_user_identities_for_connector(self.config, user_identities)
            )

            # Backwards-compatible consent preferences for old workflow
            consent_preference_schemas: List[Consent] = [
                Consent(**pref) for pref in privacy_request.consent_preferences or []
            ]

            # Privacy preferences for new workflow
            filtered_privacy_preference_records: List[PrivacyPreferenceHistory] = (
                filter_privacy_preferences_for_propagation(
                    self.configuration.system, privacy_request.privacy_preferences
                )
            )
            filtered_privacy_request_schemas: List[
                MinimalPrivacyPreferenceHistorySchema
            ] = [
                MinimalPrivacyPreferenceHistorySchema.from_orm(privacy_pref)
                for privacy_pref in filtered_privacy_preference_records
            ]

            if filtered_user_identities and (
                consent_preference_schemas or filtered_privacy_preference_records
            ):
                cache_initial_status_and_identities_for_consent_reporting(
                    db=db,
                    privacy_request=privacy_request,
                    connection_config=self.configuration,
                    relevant_preferences=filtered_privacy_preference_records,
                    relevant_user_identities=filtered_user_identities,
                )

                batched_consent_preferences.append(
                    ConsentPreferencesByUser(
                        identities=filtered_user_identities,
                        consent_preferences=consent_preference_schemas,
                        privacy_preferences=filtered_privacy_request_schemas,
                    )
                )
            else:
                skipped_privacy_requests.append(privacy_request.id)
                self.add_skipped_log(db, privacy_request)

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
            for privacy_request in privacy_requests:
                if privacy_request.id not in skipped_privacy_requests:
                    self.add_errored_log(db, privacy_request)
            raise

        for privacy_request in privacy_requests:
            if privacy_request.id not in skipped_privacy_requests:
                ExecutionLog.create(
                    db=db,
                    data={
                        "connection_key": self.configuration.key,
                        "dataset_name": self.configuration.name,
                        "privacy_request_id": privacy_request.id,
                        "collection_name": self.configuration.name,
                        "action_type": ActionType.consent,
                        "status": ExecutionLogStatus.complete,
                        "message": f"Consent email instructions dispatched for '{self.configuration.name}'",
                    },
                )
                add_complete_system_status_for_consent_reporting(
                    db, privacy_request, self.configuration
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
