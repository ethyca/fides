from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional

from sqlalchemy.orm import Query, Session

from fides.api.ctl.sql_models import Organization  # type: ignore[attr-defined]
from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.connectionconfig import ConnectionConfig, ConnectionTestStatus
from fides.api.ops.models.messaging import MessagingConfig
from fides.api.ops.schemas.messaging.messaging import MessagingServiceType
from fides.api.ops.service.connectors.base_connector import DB_CONNECTOR_TYPE
from fides.core.config import CONFIG


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
