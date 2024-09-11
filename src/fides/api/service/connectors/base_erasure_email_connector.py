from typing import Any, Dict, List

from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.policy import Rule
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
)
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettings,
    BaseEmailSchema,
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
    ConnectionType.dynamic_erasure_email,
]


class BaseErasureEmailConnector(BaseEmailConnector):
    """Generic Email Erasure Connector that can be overridden for specific vendors"""

    def get_config(self, configuration: ConnectionConfig) -> BaseEmailSchema:
        raise NotImplementedError("Get config method must be implemented in a subclass")

    @property
    def identities_for_test_email(self) -> Dict[str, Any]:
        return {"email": "test_email@example.com"}

    @property
    def required_identities(self) -> List[str]:
        return get_identity_types_for_connector(self.config)

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        self.config = self.get_config(configuration)

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
    email_secrets: BaseEmailSchema,
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
    secrets: BaseEmailSchema, user_identities: Dict[str, Any]
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
