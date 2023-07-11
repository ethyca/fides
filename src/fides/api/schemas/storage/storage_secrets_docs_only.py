from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.storage.storage import StorageSecretsS3


class StorageSecretsS3Docs(StorageSecretsS3, NoValidationSchema):
    """The secrets required to connect to S3, for documentation"""


possible_storage_secrets = StorageSecretsS3Docs
