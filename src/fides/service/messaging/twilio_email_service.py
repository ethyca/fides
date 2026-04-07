import json
from typing import Optional

import sendgrid
from loguru import logger
from sendgrid.helpers.mail import Content, Email, Mail, Personalization, TemplateId, To

from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    EmailForActionType,
    MessagingServiceDetailsTwilioEmail,
    MessagingServiceSecretsTwilioEmail,
)
from fides.api.util.logger import Pii

# TODO: this one should be imported
EMAIL_TEMPLATE_NAME = "fides"


class TwilioEmailException(Exception):
    pass


class TwilioEmailService:
    def __init__(self, messaging_config: MessagingConfig):
        self.messaging_config_details = (
            MessagingServiceDetailsTwilioEmail.model_validate(messaging_config.details)
        )
        self.messaging_config_secrets = (
            MessagingServiceSecretsTwilioEmail.model_validate(messaging_config.secrets)
        )

    def send_email(
        self,
        message: EmailForActionType,
        to: str,
    ) -> None:
        """Dispatches email using twilio sendgrid"""
        # validate_config(messaging_config, "Twilio email")

        try:
            sg = sendgrid.SendGridAPIClient(
                api_key=self.messaging_config_secrets.twilio_api_key
            )

            # the pagination via the client actually doesn't work
            # in lieu of over-engineering this we can manually call
            # the next page if/when we hit the limit here
            response = sg.client.templates.get(
                query_params={"generations": "dynamic", "page_size": 200}
            )
            template_test = self._get_template_id_if_exists(
                json.loads(response.body), EMAIL_TEMPLATE_NAME
            )

            from_email = Email(self.messaging_config_details.twilio_email_from)
            to_email = To(to.strip())
            subject = message.subject
            mail = self._compose_twilio_mail(
                from_email, to_email, subject, message.body, template_test
            )

            response = sg.client.mail.send.post(request_body=mail.get())
            if response.status_code >= 400:
                logger.error(
                    "Email failed to send: %s: %s",
                    response.status_code,
                    Pii(str(response.body)),
                )
                raise TwilioEmailException(
                    f"Email failed to send: {response.status_code}, {Pii(str(response.body))}"
                )
        except Exception as e:
            logger.error("Email failed to send: {}", Pii(str(e)))
            raise TwilioEmailException(f"Email failed to send due to: {Pii(e)}")

    def _get_template_id_if_exists(
        self, templates_response: dict[str, list], template_name: str
    ) -> Optional[str]:
        """
        Checks to see if a SendGrid template exists for Fides, returning the id if so
        """
        for template in templates_response["result"]:
            if template["name"].lower() == template_name.lower():
                return template["id"]
        return None

    def _compose_twilio_mail(
        self,
        from_email: Email,
        to_email: To,
        subject: str,
        message_body: str,
        template_test: Optional[str] = None,
    ) -> Mail:
        """
        Returns the Mail object to send, if a template is passed composes the Mail
        appropriately with the template ID and paramaterized message body.
        """
        if template_test:
            mail = Mail(from_email=from_email, subject=subject)
            mail.template_id = TemplateId(template_test)
            personalization = Personalization()
            personalization.dynamic_template_data = {"fides_email_body": message_body}
            personalization.add_email(to_email)
            mail.add_personalization(personalization)
        else:
            content = Content("text/html", message_body)
            mail = Mail(from_email, to_email, subject, content)
        return mail
