from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.ctl.sql_models import Organization  # type: ignore[attr-defined]
from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.ops.models.messaging import MessagingConfig
from fides.api.ops.models.policy import ActionType, Rule
from fides.api.ops.models.privacy_request import (
    ErasureRequestBodyParams,
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
)
from fides.api.ops.schemas.connection_configuration import EmailSchema
from fides.api.ops.schemas.messaging.messaging import (
    MessagingActionType,
    MessagingServiceType,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors.base_connector import LimitedConnector
from fides.api.ops.service.messaging.message_dispatch_service import dispatch_message

ERASURE_EMAIL_CONNECTOR_TYPES = [ConnectionType.attentive]


class EmailConnector(LimitedConnector):
    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        self.config = EmailSchema(**configuration.secrets or {})

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Sends an email to the "test_email" configured, just to establish that the email workflow is working.
        """
        logger.info("Starting test connection to {}", self.configuration.key)

        db = Session.object_session(self.configuration)
        email_service: Optional[str] = _get_email_messaging_config_service_type(db=db)

        try:
            # synchronous for now since failure to send is considered a connection test failure
            dispatch_message(
                db=db,
                action_type=MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT,
                to_identity=Identity(email=self.config.test_email_address),
                service_type=email_service,
                message_body_params=ErasureRequestBodyParams(
                    controller="Test Organization",
                    third_party_vendor_name=self.config.third_party_vendor_name,
                    identities=["test@ethyca.com"],
                ),
            )
        except MessageDispatchException as exc:
            logger.info("Email connector test failed with exception {}", exc)
            return ConnectionTestStatus.failed
        return ConnectionTestStatus.succeeded

    def needs_email(
        self, user_identities: Dict[str, Any], privacy_request: PrivacyRequest
    ) -> bool:
        """Schedules an erasure email for erasure privacy requests containing email identities"""
        erasure_rules: List[Rule] = privacy_request.policy.get_rules_for_action(
            action_type=ActionType.erasure
        )
        return bool(erasure_rules and "email" in user_identities.keys())

    def send_erasure_email(self, privacy_requests: Query) -> None:
        identities = set()
        for privacy_request in privacy_requests:
            identities.add(privacy_request.get_cached_identity_data().get("email"))

        db = Session.object_session(self.configuration)
        email_service: Optional[str] = _get_email_messaging_config_service_type(db=db)

        try:
            dispatch_message(
                db=db,
                action_type=MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT,
                to_identity=Identity(email=self.config.recipient_email_address),
                service_type=email_service,
                message_body_params=ErasureRequestBodyParams(
                    controller=_get_org_name(db),
                    third_party_vendor_name=self.config.third_party_vendor_name,
                    identities=identities,
                ),
            )

            # create an audit event for each privacy request ID
            for privacy_request in privacy_requests:
                ExecutionLog.create(
                    db=db,
                    data={
                        "connection_key": self.configuration.key,
                        "dataset_name": self.configuration.name,
                        "privacy_request_id": privacy_request.id,
                        "action_type": ActionType.erasure,
                        "status": ExecutionLogStatus.complete,
                        "message": f"Erasure email instructions dispatched for {self.config.third_party_vendor_name}",
                    },
                )
        except MessageDispatchException as exc:
            logger.info("Erasure email failed with exception {}", exc)
            raise


def _get_org_name(db: Session) -> str:
    org: Optional[Organization] = (
        db.query(Organization).order_by(Organization.created_at.desc()).first()
    )

    if not org or not org.name:
        raise MessageDispatchException(
            "Cannot send an email requesting data erasure to third-party vendor. "
            "No organization name found."
        )

    return org.name


def _get_email_messaging_config_service_type(db: Session) -> Optional[str]:
    """
    Email connectors require that an email messaging service has been configured.
    Prefers Twilio if both Twilio email AND Mailgun has been configured.
    """
    messaging_configs: Optional[List[MessagingConfig]] = MessagingConfig.query(
        db=db
    ).all()
    if not messaging_configs:
        # let messaging dispatch service handle non-existent service
        return None
    twilio_email_config = next(
        (
            config
            for config in messaging_configs
            if config.service_type == MessagingServiceType.TWILIO_EMAIL
        ),
        None,
    )
    mailgun_config = next(
        (
            config
            for config in messaging_configs
            if config.service_type == MessagingServiceType.MAILGUN
        ),
        None,
    )
    if twilio_email_config:
        # we prefer twilio over mailgun
        return MessagingServiceType.TWILIO_EMAIL.value
    if mailgun_config:
        return MessagingServiceType.MAILGUN.value
    return None
