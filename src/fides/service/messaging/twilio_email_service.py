import sendgrid
import json
from typing import Literal, Optional

from loguru import logger

from sendgrid.helpers.mail import Content, Email, Mail, Personalization, TemplateId, To

from fides.service.messaging.base_messaging_provider_service import (
    BaseMessageProviderService,
    EMAIL_TEMPLATE_NAME,
)
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    MessagingServiceDetailsTwilioEmail,
    MessagingServiceSecretsTwilioEmail,
    EmailForActionType,
)

from fides.api.util.logger import Pii
from fides.api.common_exceptions import MessageDispatchException


class TwilioEmailService(BaseMessageProviderService):
    provider_name: Literal["Twilio Email"] = "Twilio Email"

    def __init__(self, messaging_config: MessagingConfig):
        super().__init__(messaging_config)

        self.messaging_config_details = (
            MessagingServiceDetailsTwilioEmail.model_validate(messaging_config.details)
        )
        self.messaging_config_secrets = (
            MessagingServiceSecretsTwilioEmail.model_validate(messaging_config.secrets)
        )
        self._sg_client = sendgrid.SendGridAPIClient(
            api_key=self.messaging_config_secrets.twilio_api_key
        ).client

    def _get_template_id_if_exists(
        self,
    ) -> Optional[str]:
        """
        Checks to see if a SendGrid template exists for Fides, returning the id if so
        """
        # the pagination via the client actually doesn't work
        # in lieu of over-engineering this we can manually call
        # the next page if/when we hit the limit here
        response = self._sg_client.templates.get(
            query_params={"generations": "dynamic", "page_size": 200}
        )

        processed_response = json.loads(response.body)

        for template in processed_response["result"]:
            if template["name"].lower() == EMAIL_TEMPLATE_NAME.lower():
                return template["id"]
        return None

    def _compose_twilio_mail(
        self,
        message: EmailForActionType,
        to_email: To,
        template_id: Optional[str] = None,
    ):
        """
        Returns the Mail object to send, if a template is passed composes the Mail
        appropriately with the template ID and paramaterized message body.
        """
        from_email = Email(self.messaging_config_details.twilio_email_from)

        subject = message.subject
        message_body = message.body

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

    def send_message(self, message: EmailForActionType, to: str):
        try:
            template_test = self._get_template_id_if_exists()

            to_email = To(to.strip())
            mail = self._compose_twilio_mail(
                message=message, to_email=to_email, template_id=template_test
            )

            response = self._sg_client.mail.send.post(request_body=mail.get())
            if response.status_code >= 400:
                raise MessageDispatchException(
                    f"Email failed to send: {response.status_code}, {Pii(str(response.body))}"
                )
        except Exception as e:
            logger.error("Email failed to send: {}", Pii(str(e)))
            raise MessageDispatchException(f"Email failed to send due to: {Pii(e)}")
