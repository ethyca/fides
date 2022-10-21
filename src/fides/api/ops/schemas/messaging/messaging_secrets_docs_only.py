from typing import Union

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.messaging.messaging import EmailServiceSecretsMailgun


class EmailSecretsMailgunDocs(EmailServiceSecretsMailgun, NoValidationSchema):
    """The secrets required to connect to Mailgun, for documentation"""


possible_email_secrets = Union[EmailSecretsMailgunDocs]
