from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.models.policy import Rule
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
)
from fides.api.schemas.connection_configuration import EmailSchema
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettings,
    IdentityTypes,
)
from fides.api.schemas.messaging.messaging import (
    ErasureRequestBodyParams,
    MessagingActionType,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors.base_email_connector import (
    BaseEmailConnector,
    get_email_messaging_config_service_type,
    get_org_name,
)
from fides.api.service.messaging.message_dispatch_service import dispatch_message
from fides.config import get_config

CONFIG = get_config()

ERASURE_EMAIL_CONNECTOR_TYPES = [
    ConnectionType.generic_erasure_email,
    ConnectionType.attentive,
]


class GenericErasureEmailConnector(BaseEmailConnector):
    """Generic Email Erasure Connector that can be overridden for specific vendors"""

    @property
    def identities_for_test_email(self) -> Dict[str, Any]:
        return {"email": "test_email@example.com"}

    @property
    def required_identities(self) -> List[str]:
        return get_identity_types_for_connector(self.config)

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        self.config = EmailSchema(**configuration.secrets or {})

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Sends an email to the "test_email" configured, just to establish that the email workflow is working.
        """
        logger.info("Starting test connection to {}", self.configuration.key)

        db = Session.object_session(self.configuration)

        try:
            if not self.config.test_email_address:
                raise MessageDispatchException(
                    f"Cannot test connection. No test email defined for {self.configuration.name}"
                )
            # synchronous for now since failure to send is considered a connection test failure
            send_single_erasure_email(
                db=db,
                subject_email=self.config.test_email_address,
                subject_name=self.config.third_party_vendor_name,
                batch_identities=list(self.identities_for_test_email.values()),
                test_mode=True,
            )
        except MessageDispatchException as exc:
            logger.info("Email connector test failed with exception {}", exc)
            return ConnectionTestStatus.failed
        return ConnectionTestStatus.succeeded

    def needs_email(
        self, user_identities: Dict[str, Any], privacy_request: PrivacyRequest
    ) -> bool:
        """Schedules an erasure email for erasure privacy requests containing the required identities"""
        erasure_rules: List[Rule] = privacy_request.policy.get_rules_for_action(
            action_type=ActionType.erasure
        )
        return bool(
            erasure_rules
            and filter_user_identities_for_connector(self.config, user_identities)
        )

    def batch_email_send(self, privacy_requests: Query) -> None:
        skipped_privacy_requests: List[str] = []
        batched_identities: List[str] = []
        db = Session.object_session(self.configuration)

        for privacy_request in privacy_requests:
            user_identities: Dict[str, Any] = privacy_request.get_cached_identity_data()
            filtered_user_identities: Dict[str, Any] = (
                filter_user_identities_for_connector(self.config, user_identities)
            )
            if filtered_user_identities:
                batched_identities.extend(filtered_user_identities.values())
            else:
                skipped_privacy_requests.append(privacy_request.id)
                self.add_skipped_log(db, privacy_request)

        if not batched_identities:
            logger.info(
                "Skipping erasure email send for connector: '{}'. "
                "No corresponding user identities found for pending privacy requests.",
                self.configuration.name,
            )
            return

        logger.info(
            "Sending batched erasure email for connector {}...",
            self.configuration.name,
        )

        try:
            send_single_erasure_email(
                db=db,
                subject_email=self.config.recipient_email_address,
                subject_name=self.config.third_party_vendor_name,
                batch_identities=batched_identities,
                test_mode=False,
            )
        except MessageDispatchException as exc:
            logger.info("Erasure email failed with exception {}", exc)
            raise

        # create an audit event for each privacy request ID
        for privacy_request in privacy_requests:
            if privacy_request.id not in skipped_privacy_requests:
                ExecutionLog.create(
                    db=db,
                    data={
                        "connection_key": self.configuration.key,
                        "dataset_name": self.configuration.name,
                        "collection_name": self.configuration.name,
                        "privacy_request_id": privacy_request.id,
                        "action_type": ActionType.erasure,
                        "status": ExecutionLogStatus.complete,
                        "message": f"Erasure email instructions dispatched for '{self.configuration.name}'",
                    },
                )

    def add_skipped_log(self, db: Session, privacy_request: PrivacyRequest) -> None:
        """Add skipped log for the email connector to the privacy request"""
        ExecutionLog.create(
            db=db,
            data={
                "connection_key": self.configuration.key,
                "dataset_name": self.configuration.name,
                "collection_name": self.configuration.name,
                "privacy_request_id": privacy_request.id,
                "action_type": ActionType.erasure,
                "status": ExecutionLogStatus.skipped,
                "message": f"Erasure email skipped for '{self.configuration.name}'",
            },
        )


def get_identity_types_for_connector(
    email_secrets: EmailSchema,
) -> List[str]:
    """Return a list of identity types we need to email to the third party vendor."""
    advanced_settings: AdvancedSettings = email_secrets.advanced_settings
    identity_types: IdentityTypes = advanced_settings.identity_types
    flattened_list: List[str] = []

    if identity_types.email:
        flattened_list.append("email")
    if identity_types.phone_number:
        flattened_list.append("phone_number")

    return flattened_list


def filter_user_identities_for_connector(
    secrets: EmailSchema, user_identities: Dict[str, Any]
) -> Dict[str, Any]:
    """Filter identities to just those specified for a given connector"""
    required_identities: List[str] = get_identity_types_for_connector(secrets)
    return {
        identity_type: user_identities.get(identity_type)
        for identity_type in required_identities
        if user_identities.get(identity_type)
    }


def send_single_erasure_email(
    db: Session,
    subject_email: str,
    subject_name: str,
    batch_identities: List[str],
    test_mode: bool = False,
) -> None:
    """Sends a single erasure email"""

    org_name = get_org_name(db)

    dispatch_message(
        db=db,
        action_type=MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT,
        to_identity=Identity(email=subject_email),
        service_type=get_email_messaging_config_service_type(db=db),
        message_body_params=ErasureRequestBodyParams(
            controller=org_name,
            third_party_vendor_name=subject_name,
            identities=batch_identities,
        ),
        subject_override=f"{'Test notification' if test_mode else 'Notification'} "
        f"of user erasure requests from {org_name}",
    )
