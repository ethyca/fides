from typing import Union

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.messaging.messaging import (
    MessagingServiceSecretsMailgun,
    MessagingServiceSecretsTwilio,
)


class MessagingSecretsMailgunDocs(MessagingServiceSecretsMailgun, NoValidationSchema):
    """The secrets required to connect to Mailgun, for documentation"""


class MessagingSecretsTwilioDocs(MessagingServiceSecretsTwilio, NoValidationSchema):
    """The secrets required to connect to Twilio, for documentation"""


possible_messaging_secrets = Union[
    MessagingSecretsMailgunDocs, MessagingSecretsTwilioDocs
]
