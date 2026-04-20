import json

import sendgrid
from loguru import logger
from sendgrid.helpers.mail import Content, Email, Mail, Personalization, TemplateId, To

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


class TwilioEmailService(BaseEmailProviderService):
    """Dispatches email using Twilio SendGrid."""

    provider_name = "Twilio email"

    def __init__(self, messaging_config: MessagingConfig):
        super().__init__(messaging_config)
        self.api_key = messaging_config.secrets[
            MessagingServiceSecrets.TWILIO_API_KEY.value
        ]
        self.from_email = messaging_config.details[
            MessagingServiceDetails.TWILIO_EMAIL_FROM.value
        ]

    def send_email(self, to: str, message: EmailForActionType) -> None:
        try:
            sg = sendgrid.SendGridAPIClient(api_key=self.api_key)

            response = sg.client.templates.get(
                query_params={"generations": "dynamic", "page_size": 200}
            )
            template_id = self._get_template_id_if_exists(
                json.loads(response.body), EMAIL_TEMPLATE_NAME
            )

            from_email = Email(self.from_email)
            to_email = To(to.strip())
            mail = self._compose_mail(
                from_email, to_email, message.subject, message.body, template_id
            )

            response = sg.client.mail.send.post(request_body=mail.get())
            if response.status_code >= 400:
                logger.error(
                    "Email failed to send: %s: %s",
                    response.status_code,
                    str(response.body),
                )
                raise MessageDispatchException(
                    f"Email failed to send: {response.status_code}, {str(response.body)}"
                )
        except MessageDispatchException:
            raise
        except Exception as exc:
            logger.error("Email failed to send: {}", str(exc))
            raise MessageDispatchException(f"Email failed to send due to: {str(exc)}")

    @staticmethod
    def _get_template_id_if_exists(
        templates_response: dict[str, list], template_name: str
    ) -> str | None:
        """Returns the SendGrid template ID if a template with the given name exists."""
        for template in templates_response["result"]:
            if template["name"].lower() == template_name.lower():
                return template["id"]
        return None

    @staticmethod
    def _compose_mail(
        from_email: Email,
        to_email: To,
        subject: str,
        message_body: str,
        template_id: str | None = None,
    ) -> Mail:
        """Composes a SendGrid Mail object, using a template if one exists."""
        if template_id:
            mail = Mail(from_email=from_email, subject=subject)
            mail.template_id = TemplateId(template_id)
            personalization = Personalization()
            personalization.dynamic_template_data = {"fides_email_body": message_body}
            personalization.add_email(to_email)
            mail.add_personalization(personalization)
        else:
            content = Content("text/html", message_body)
            mail = Mail(from_email, to_email, subject, content)
        return mail
