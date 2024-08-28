from typing import Any, Dict, Optional

from boto3 import Session
from botocore.exceptions import ClientError
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import AWSAuthMethod, StorageSecrets


def get_aws_session(
    auth_method: str,
    storage_secrets: Dict[StorageSecrets, Any],
    assume_role_arn: Optional[str] = None,
) -> Session:
    """
    Abstraction to retrieve an AWS Session using secrets.

    If an `assume_role_arn` is provided, the secrets will be used to
    assume that role and return a Session instantiated with that role.
    """
    sts_client = None
    if auth_method == AWSAuthMethod.SECRET_KEYS.value:
        if storage_secrets is None:
            err_msg = "Storage secrets not found for S3 storage."
            logger.warning(err_msg)
            raise StorageUploadError(err_msg)

        session = Session(
            aws_access_key_id=storage_secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value],  # type: ignore
            aws_secret_access_key=storage_secrets[
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value  # type: ignore
            ],
            region_name=storage_secrets.get("region_name"),  # type: ignore
        )
    elif auth_method == AWSAuthMethod.AUTOMATIC.value:
        session = Session()
        logger.info("Successfully created automatic session")
    else:
        logger.error("Auth method not supported for S3: {}", auth_method)
        raise ValueError(f"Auth method not supported for S3: {auth_method}")

    # Check that credentials are valid
    sts_client = session.client("sts")
    sts_client.get_caller_identity()

    if assume_role_arn:
        try:
            response = sts_client.assume_role(
                RoleArn=assume_role_arn, RoleSessionName="FidesAssumeRoleSession"
            )
            temp_credentials = response["Credentials"]
            logger.info(
                f"Assumed role {assume_role_arn} and got temporary credentials."
            )
            return Session(
                aws_access_key_id=temp_credentials["AccessKeyId"],
                aws_secret_access_key=temp_credentials["SecretAccessKey"],
                aws_session_token=temp_credentials["SessionToken"],
            )
        except ClientError as error:
            logger.exception(
                f"Failed to assume assume role {assume_role_arn}. Error: {error.response['Error']['Message']}"
            )
            raise
    else:
        return session
