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


class MailchimpTransactionalService(BaseEmailProviderService):
    """Dispatches email using Mailchimp Transactional (Mandrill)."""

    provider_name = "Mailchimp Transactional"

    def __init__(self, messaging_config: MessagingConfig):
        super().__init__(messaging_config)
        self.from_email = messaging_config.details[
            MessagingServiceDetails.EMAIL_FROM.value
        ]
        self.api_key = messaging_config.secrets[
            MessagingServiceSecrets.MAILCHIMP_TRANSACTIONAL_API_KEY.value
        ]

    def send_email(self, to: str, message: EmailForActionType) -> None:
        data = json.dumps(
            {
                "key": self.api_key,
                "message": {
                    "from_email": self.from_email,
                    "subject": message.subject,
                    "html": message.body,
                    "to": [{"email": to.strip(), "type": "to"}],
                },
            }
        )

        response = requests.post(
            "https://mandrillapp.com/api/1.0/messages/send",
            headers={"Content-Type": "application/json"},
            data=data,
            timeout=10,
        )
        if not response.ok:
            logger.error(
                "Email failed to send with status code: %s", response.status_code
            )
            raise MessageDispatchException(
                f"Email failed to send with status code {response.status_code}"
            )

        send_data = response.json()[0]
        email_rejected = send_data.get("status", "rejected") == "rejected"
        if email_rejected:
            reason = send_data.get("reject_reason", "Fides Error")
            explanations = {
                "soft-bounce": "A temporary error occured with the target inbox. For example, this inbox could be full. See https://mailchimp.com/developer/transactional/docs/reputation-rejections/#bounces for more info.",
                "hard-bounce": "A permanent error occured with the target inbox. See https://mailchimp.com/developer/transactional/docs/reputation-rejections/#bounces for more info.",
                "recipient-domain-mismatch": f"You are not authorised to send email to this domain from {self.from_email}.",
                "unsigned": f"The sending domain for {self.from_email} has not been fully configured for Mailchimp Transactional. See https://mailchimp.com/developer/transactional/docs/authentication-delivery/#authentication/ for more info.",
            }
            explanation = explanations.get(reason, "")
            raise MessageDispatchException(
                f"Verification email unable to send due to reason: {reason}. {explanation}"
            )
