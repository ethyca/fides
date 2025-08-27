from typing import Any, Dict, Optional

from boto3 import Session
from botocore.config import Config
from botocore.exceptions import ClientError
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import AWSAuthMethod, StorageSecrets
from fides.config import CONFIG


def get_aws_session(
    auth_method: str,
    storage_secrets: Optional[Dict[StorageSecrets, Any]],
    assume_role_arn: Optional[str] = None,
) -> Session:
    """
    Abstraction to retrieve an AWS Session using secrets.

    If an `assume_role_arn` is provided, the secrets will be used to
    assume that role and return a Session instantiated with that role.
    """
    if storage_secrets is None:
        # set to an empty dict to allow for more dynamic code downstream
        storage_secrets = {}

    stored_region_name = storage_secrets.get("region_name")  # type: ignore
    stored_assume_role_arn: Optional[str] = storage_secrets.get("assume_role_arn")  # type: ignore

    if auth_method == AWSAuthMethod.SECRET_KEYS.value:
        if not storage_secrets:
            err_msg = "Storage secrets not found for S3 storage."
            logger.warning(err_msg)
            raise StorageUploadError(err_msg)

        session = Session(
            aws_access_key_id=storage_secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value],  # type: ignore
            aws_secret_access_key=storage_secrets[
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value  # type: ignore
            ],
            region_name=stored_region_name,
        )
    elif auth_method == AWSAuthMethod.AUTOMATIC.value:
        session = Session(region_name=stored_region_name)
        logger.info("Successfully created automatic session")
    else:
        logger.error("AWS auth method not supported: {}", auth_method)
        raise ValueError(f"AWS auth method not supported: {auth_method}")

    # Check that credentials are valid
    sts_client = session.client("sts")
    sts_client.get_caller_identity()

    target_assume_role_arn = assume_role_arn or stored_assume_role_arn
    if target_assume_role_arn:
        try:
            return get_assumed_role_session(
                target_assume_role_arn,
                sts_client,
                stored_region_name,
            )
        except ClientError as error:
            logger.exception(
                f"Failed to assume assume role {assume_role_arn}. Error: {error.response['Error']['Message']}"
            )
            raise
    else:
        return session


def get_assumed_role_session(
    assume_role_arn: str, sts_client: Any, region_name: Optional[str] = None
) -> Session:
    response = sts_client.assume_role(
        RoleArn=assume_role_arn, RoleSessionName="FidesAssumeRoleSession"
    )
    temp_credentials = response["Credentials"]
    logger.info(f"Assumed role {assume_role_arn} and got temporary credentials.")
    return Session(
        aws_access_key_id=temp_credentials["AccessKeyId"],
        aws_secret_access_key=temp_credentials["SecretAccessKey"],
        aws_session_token=temp_credentials["SessionToken"],
        region_name=region_name,
    )


def get_s3_client(
    auth_method: str,
    storage_secrets: Optional[Dict[StorageSecrets, Any]],
    assume_role_arn: Optional[str] = None,
) -> Session:
    """
    Abstraction to retrieve an AWS S3 client using secrets.

    If an `assume_role_arn` is provided, the secrets will be used to
    assume that role and return a Session instantiated with that role.

    If no `assume_role_arn` is provided, and `aws_s3_assume_role_arn` is
    configured in the global `credentials.storage` config, then the secrets
    will be used to assume that role and return a Session instantiated with
    that role.
    """

    configured_assume_role_arn = CONFIG.credentials.get(  # pylint: disable=no-member
        "storage", {}
    ).get(  # pylint: disable=no-member
        "aws_s3_assume_role_arn"
    )
    session = get_aws_session(
        auth_method=auth_method,
        storage_secrets=storage_secrets,
        assume_role_arn=assume_role_arn or configured_assume_role_arn,
    )

    # Configure S3 client to use signature version 4 for KMS compatibility
    s3_config = Config(signature_version="s3v4")
    return session.client("s3", config=s3_config)
