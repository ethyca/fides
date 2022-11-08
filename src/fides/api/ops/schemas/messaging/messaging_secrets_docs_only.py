from typing import Union

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.messaging.messaging import (
    MessagingServiceSecretsMailgun,
    MessagingServiceSecretsTwilioEmail,
    MessagingServiceSecretsTwilioSMS,
)


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


possible_messaging_secrets = Union[
    MessagingSecretsMailgunDocs,
    MessagingSecretsTwilioSMSDocs,
    MessagingSecretsTwilioEmailDocs,
]
