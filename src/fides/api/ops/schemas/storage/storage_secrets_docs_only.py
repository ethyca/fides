from typing import Union

from fidesctl.api.ops.schemas.base_class import NoValidationSchema
from fidesctl.api.ops.schemas.storage.storage import (
    StorageSecretsOnetrust,
    StorageSecretsS3,
)


class StorageSecretsS3Docs(StorageSecretsS3, NoValidationSchema):
    """The secrets required to connect to S3, for documentation"""


class StorageSecretsOnetrustDocs(StorageSecretsOnetrust, NoValidationSchema):
    """The secrets required to send results to Onetrust, for documentation"""


possible_storage_secrets = Union[StorageSecretsS3Docs, StorageSecretsOnetrustDocs]
