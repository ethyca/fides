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
    EMAIL_TEMPLATE_NAME,
    BaseEmailProviderService,
)


class MailgunService(BaseEmailProviderService):
    """Dispatches email using Mailgun."""

    provider_name = "Mailgun"

    def __init__(self, messaging_config: MessagingConfig):
        super().__init__(messaging_config)
        self.domain = self._get_detail(MessagingServiceDetails.DOMAIN)
        self.api_key = self._get_secret(MessagingServiceSecrets.MAILGUN_API_KEY)
        is_eu = self.messaging_config.details.get(
            MessagingServiceDetails.IS_EU_DOMAIN.value, False
        )
        self.base_url = (
            "https://api.eu.mailgun.net" if is_eu else "https://api.mailgun.net"
        )
        self.api_version = self._get_detail(MessagingServiceDetails.API_VERSION)

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

            # Threading / envelope headers
            data.update(self.get_threading_headers(message, header_prefix="h:"))
            if message.body_text:
                data["text"] = message.body_text

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
