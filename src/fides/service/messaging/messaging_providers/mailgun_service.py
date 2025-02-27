import requests
import json
from typing import Literal

from loguru import logger

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    MessagingServiceDetailsMailgun,
    MessagingServiceSecretsMailgun,
    EmailForActionType,
)

from fides.service.messaging.messaging_providers.base_messaging_provider_service import (
    EMAIL_TEMPLATE_NAME,
    BaseEmailProviderService,
)
from fides.api.util.logger import Pii


class MailgunException(Exception):
    pass


class MailgunService(BaseEmailProviderService):
    provider_name: Literal["Mailgun"] = "Mailgun"

    def __init__(self, messaging_config: MessagingConfig):
        super().__init__(messaging_config)

        self.messaging_config_details = MessagingServiceDetailsMailgun.model_validate(
            messaging_config.details
        )
        self.messaging_config_secrets = MessagingServiceSecretsMailgun.model_validate(
            messaging_config.secrets
        )

    def _get_base_url(self) -> str:
        return (
            "https://api.mailgun.net"
            if self.messaging_config_details.is_eu_domain is False
            else "https://api.eu.mailgun.net"
        )

    def _send_mailgun_email(self, data: dict) -> None:
        base_url = self._get_base_url()
        domain = self.messaging_config_details.domain

        response = requests.post(
            f"{base_url}/{self.messaging_config_details.api_version}/{domain}/messages",
            auth=("api", self.messaging_config_secrets.mailgun_api_key),
            data=data,
        )

        if not response.ok:
            raise MailgunException(
                f"Email failed to send with status code {response.status_code}"
            )

    def _check_template_exists(self) -> bool:
        base_url = self._get_base_url()
        domain = self.messaging_config_details.domain

        # Check if a fides template exists
        template_test = requests.get(
            f"{base_url}/{self.messaging_config_details.api_version}/{domain}/templates/{EMAIL_TEMPLATE_NAME}",
            auth=(
                "api",
                self.messaging_config_secrets.mailgun_api_key,
            ),
        )

        return template_test.status_code == 200

    def send_email(
        self,
        to: str,
        message: EmailForActionType,
    ) -> None:
        """
        Sends an email using the Mailgun API.
        """

        data = {
            "from": f"<mailgun@{self.messaging_config_details.domain}>",
            "to": [to.strip()],
            "subject": message.subject,
        }

        try:

            template_exists = self._check_template_exists()
            if template_exists:
                mailgun_variables = {
                    "fides_email_body": message.body,
                    **(message.template_variables or {}),
                }
                data["template"] = EMAIL_TEMPLATE_NAME
                data["h:X-Mailgun-Variables"] = json.dumps(mailgun_variables)
            else:
                data["html"] = message.body

            self._send_mailgun_email(data)

        except Exception as e:
            logger.error("Email failed to send: {}", Pii(str(e)))
            raise MessageDispatchException(f"Email failed to send due to: {Pii(e)}")
