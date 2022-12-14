from typing import Any, Dict

from boto3 import Session
from loguru import logger

from fides.api.ops.common_exceptions import StorageUploadError
from fides.api.ops.schemas.storage.storage import S3AuthMethod, StorageSecrets


def get_s3_session(
    auth_method: S3AuthMethod, storage_secrets: Dict[StorageSecrets, Any]
) -> Session:
    """Abstraction to retrieve s3 session using secrets"""
    if auth_method == S3AuthMethod.SECRET_KEYS.value:

        if storage_secrets is None:
            err_msg = "Storage secrets not found for S3 storage."
            logger.warning(err_msg)
            raise StorageUploadError(err_msg)

        session = Session(
            aws_access_key_id=storage_secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value],  # type: ignore
            aws_secret_access_key=storage_secrets[
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value  # type: ignore
            ],
        )

        # Check that credentials are valid
        client = session.client("sts")
        client.get_caller_identity()
        return session

    if auth_method == S3AuthMethod.AUTOMATIC.value:
        session = Session()
        logger.info("Successfully created automatic session")
        return session

    logger.error("Auth method not supported for S3: {}", auth_method)
    raise ValueError(f"Auth method not supported for S3: {auth_method}")
