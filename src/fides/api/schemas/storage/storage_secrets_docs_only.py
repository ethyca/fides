from typing import Union

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.storage.storage import StorageSecretsGCS, StorageSecretsS3


class StorageSecretsS3Docs(StorageSecretsS3, NoValidationSchema):
    """The secrets required to connect to S3, for documentation"""


class StorageSecretsGCSDocs(StorageSecretsGCS, NoValidationSchema):
    """The secrets required to connect to Google Cloud Storage, for documentation"""


possible_storage_secrets = Union[StorageSecretsS3Docs, StorageSecretsGCSDocs]
