from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, ConfigDict, model_validator

from fides.api.custom_types import PhoneNumber
from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_base_aws import (
    BaseAWSSchema,
)


class MessagingServiceSecretsMailgun(BaseModel):
    """The secrets required to connect to Mailgun."""

    mailgun_api_key: str
    model_config = ConfigDict(extra="forbid")


class MessagingServiceSecretsTwilioSMS(BaseModel):
    """The secrets required to connect to Twilio SMS."""

    twilio_account_sid: str
    twilio_auth_token: str
    twilio_messaging_service_sid: Optional[str] = None
    twilio_sender_phone_number: Optional[PhoneNumber] = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        sender_phone = values.get("twilio_sender_phone_number")
        if not values.get("twilio_messaging_service_sid") and not sender_phone:
            raise ValueError(
                "Either the twilio_messaging_service_sid or the twilio_sender_phone_number should be supplied."
            )
        return values


class MessagingServiceSecretsTwilioEmail(BaseModel):
    """The secrets required to connect to twilio email."""

    twilio_api_key: str
    model_config = ConfigDict(extra="forbid")


class MessagingServiceSecretsMailchimpTransactional(BaseModel):
    """The secrets required to connect to Mailchimp Transactional."""

    mailchimp_transactional_api_key: str
    model_config = ConfigDict(extra="forbid")


class MessagingServiceSecretsMailchimpTransactionalDocs(
    MessagingServiceSecretsMailchimpTransactional,
    NoValidationSchema,
):
    """The secrets required to connect Mailchimp Transactional, for documentation"""


class MessagingSecretsMailgunDocs(MessagingServiceSecretsMailgun, NoValidationSchema):
    """The secrets required to connect to Mailgun, for documentation"""


class MessagingSecretsTwilioSMSDocs(
    MessagingServiceSecretsTwilioSMS, NoValidationSchema
):
    """The secrets required to connect to Twilio sms, for documentation"""


class MessagingSecretsTwilioEmailDocs(
    MessagingServiceSecretsTwilioEmail, NoValidationSchema
):
    """The secrets required to connect to Twilio email, for documentation"""


class MessagingServiceSecretsAWS_SES(BaseAWSSchema):
    """The secrets required to connect to AWS SES."""

    model_config = ConfigDict(extra="forbid")


class MessagingServiceSecretsAWS_SESDocs(
    MessagingServiceSecretsAWS_SES, NoValidationSchema
):
    """The secrets required to connect to AWS SES, for documentation"""


SUPPORTED_MESSAGING_SERVICE_SECRETS = Union[
    MessagingServiceSecretsMailgun,
    MessagingServiceSecretsTwilioSMS,
    MessagingServiceSecretsTwilioEmail,
    MessagingServiceSecretsMailchimpTransactional,
    MessagingServiceSecretsAWS_SES,
]

PossibleMessagingSecrets = Union[
    MessagingSecretsMailgunDocs,
    MessagingSecretsTwilioSMSDocs,
    MessagingSecretsTwilioEmailDocs,
    MessagingServiceSecretsMailchimpTransactionalDocs,
    MessagingServiceSecretsAWS_SESDocs,
]
