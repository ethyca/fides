import json

import requests
from loguru import logger

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    EmailForActionType,
    MessagingServiceDetails,
    MessagingServiceSecrets,
)
from fides.api.service.messaging.messaging_providers.base import (
    BaseEmailProviderService,
)

EMAIL_TEMPLATE_NAME = "fides"


class MailgunService(BaseEmailProviderService):
    """Dispatches email using Mailgun."""

    provider_name = "Mailgun"

    def __init__(self, messaging_config: MessagingConfig):
        super().__init__(messaging_config)
        self.domain = messaging_config.details[MessagingServiceDetails.DOMAIN.value]
        self.api_key = messaging_config.secrets[
            MessagingServiceSecrets.MAILGUN_API_KEY.value
        ]
        is_eu = messaging_config.details[MessagingServiceDetails.IS_EU_DOMAIN.value]
        self.base_url = (
            "https://api.eu.mailgun.net" if is_eu else "https://api.mailgun.net"
        )
        self.api_version = messaging_config.details[
            MessagingServiceDetails.API_VERSION.value
        ]

    def send_email(self, to: str, message: EmailForActionType) -> None:
        try:
            template_test = requests.get(
                f"{self.base_url}/{self.api_version}/{self.domain}/templates/{EMAIL_TEMPLATE_NAME}",
                auth=("api", self.api_key),
                timeout=10,
            )

            data: dict[str, str | list[str]] = {
                "from": f"<mailgun@{self.domain}>",
                "to": [to.strip()],
                "subject": message.subject,
            }

            if template_test.status_code == 200:
                mailgun_variables = {
                    "fides_email_body": message.body,
                    **(message.template_variables or {}),
                }
                data["template"] = EMAIL_TEMPLATE_NAME
                data["h:X-Mailgun-Variables"] = json.dumps(mailgun_variables)
            else:
                data["html"] = message.body

            response = requests.post(
                f"{self.base_url}/{self.api_version}/{self.domain}/messages",
                auth=("api", self.api_key),
                data=data,
                timeout=10,
            )

            if not response.ok:
                logger.error(
                    "Email failed to send with status code: %s",
                    response.status_code,
                )
                raise MessageDispatchException(
                    f"Email failed to send with status code {response.status_code}"
                )
        except MessageDispatchException:
            raise
        except Exception as exc:
            logger.error("Email failed to send: {}", str(exc))
            raise MessageDispatchException(f"Email failed to send due to: {str(exc)}")
