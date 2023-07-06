from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional

from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.models.messaging import MessagingConfig
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.sql_models import Organization  # type: ignore[attr-defined]
from fides.api.schemas.messaging.messaging import (
    EMAIL_MESSAGING_SERVICES,
    MessagingServiceType,
)
from fides.api.service.connectors.base_connector import DB_CONNECTOR_TYPE
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy


class BaseEmailConnector(Generic[DB_CONNECTOR_TYPE], ABC):
    """
    Abstract BaseEmailConnector that operates at the Dataset Level, not the Collection level.
    """

    @property
    @abstractmethod
    def required_identities(self) -> List[str]:
        """Returns the identity types we need to supply to the third party for this connector."""

    @property
    @abstractmethod
    def identities_for_test_email(self) -> Dict[str, Any]:
        """The mock user identities that are sent in the test email to ensure the connector is working"""

    def __init__(self, configuration: ConnectionConfig):
        self.configuration = configuration
        self.hide_parameters = not CONFIG.dev_mode
        self.db_client: Optional[DB_CONNECTOR_TYPE] = None

    @abstractmethod
    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Used to send a test email to the specified email address to verify the generated email template.
        """

    @abstractmethod
    def batch_email_send(self, privacy_requests: Query) -> None:
        """
        Aggregates the identities provided by multiple privacy requests and sends them in a single batch email.
        """

    @abstractmethod
    def add_skipped_log(self, db: Session, privacy_request: PrivacyRequest) -> None:
        """Add skipped log for the email connector to a privacy request"""


def get_org_name(db: Session) -> str:
    org: Optional[Organization] = (
        db.query(Organization).order_by(Organization.created_at.desc()).first()
    )

    if not org or not org.name:
        raise MessageDispatchException(
            "Cannot send an email to third-party vendor. No organization name found."
        )

    return org.name


def get_email_messaging_config_service_type(db: Session) -> Optional[str]:
    """
    Email connectors require that an email messaging service has been configured.
    Prefers Twilio if both Twilio email AND Mailgun has been configured.
    """

    # if there's a specified messaging service type, and it's an email service, we use that
    if (
        configured_service_type := ConfigProxy(
            db
        ).notifications.notification_service_type
    ) is not None and configured_service_type in EMAIL_MESSAGING_SERVICES:
        return configured_service_type

    # if no specified messaging service type, fall back to hardcoded preference hierarchy
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
            if config.service_type == MessagingServiceType.twilio_email
        ),
        None,
    )
    if twilio_email_config:
        # First choice: use Twilio
        return MessagingServiceType.twilio_email.value

    mailgun_config = next(
        (
            config
            for config in messaging_configs
            if config.service_type == MessagingServiceType.mailgun
        ),
        None,
    )
    if mailgun_config:
        # Second choice: use Mailgun
        return MessagingServiceType.mailgun.value

    mailchimp_transactional_config = next(
        (
            config
            for config in messaging_configs
            if config.service_type == MessagingServiceType.mailchimp_transactional
        ),
        None,
    )
    if mailchimp_transactional_config:
        # Third choice: use Mailchimp Transactional
        return MessagingServiceType.mailchimp_transactional.value

    return None
