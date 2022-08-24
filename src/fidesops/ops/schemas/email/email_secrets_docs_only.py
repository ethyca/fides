from typing import Union

from fidesops.ops.schemas.base_class import NoValidationSchema
from fidesops.ops.schemas.email.email import EmailServiceSecretsMailgun


class EmailSecretsMailgunDocs(EmailServiceSecretsMailgun, NoValidationSchema):
    """The secrets required to connect to Mailgun, for documentation"""


possible_email_secrets = Union[EmailSecretsMailgunDocs]
