from typing import Union

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.messaging.messaging import (
    MessagingServiceSecretsAWS_SES,
    MessagingServiceSecretsMailchimpTransactional,
    MessagingServiceSecretsMailgun,
    MessagingServiceSecretsTwilioEmail,
    MessagingServiceSecretsTwilioSMS,
)


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


class MessagingServiceSecretsAWS_SESDocs(
    MessagingServiceSecretsAWS_SES, NoValidationSchema
):
    """The secrets required to connect to AWS SES, for documentation"""


possible_messaging_secrets = Union[
    MessagingSecretsMailgunDocs,
    MessagingSecretsTwilioSMSDocs,
    MessagingSecretsTwilioEmailDocs,
    MessagingServiceSecretsMailchimpTransactionalDocs,
    MessagingServiceSecretsAWS_SESDocs,
]
