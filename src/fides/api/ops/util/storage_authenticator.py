import logging
from typing import Any, Dict

import boto3
import requests
from boto3 import Session
from requests import Response

from fidesops.ops.common_exceptions import StorageUploadError
from fidesops.ops.schemas.storage.storage import S3AuthMethod, StorageSecrets
from fidesops.ops.schemas.third_party.onetrust import OneTrustOAuthResponse

logger = logging.getLogger(__name__)


def get_s3_session(
    auth_method: S3AuthMethod, storage_secrets: Dict[StorageSecrets, Any]
) -> Session:
    """Abstraction to retrieve s3 session using secrets"""
    if auth_method == S3AuthMethod.SECRET_KEYS.value:

        if storage_secrets is None:
            err_msg = "Storage secrets not found for S3 storage."
            logger.warning(err_msg)
            raise StorageUploadError(err_msg)

        session = boto3.session.Session(
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
        session = boto3.session.Session()
        logger.info("Successfully created automatic session")
        return session

    logger.error("Auth method not supported for S3: %s", auth_method)
    raise ValueError(f"Auth method not supported for S3: {auth_method}")


def get_onetrust_access_token(client_id: str, client_secret: str, hostname: str) -> str:
    """Retrieves onetrust access token using secrets"""
    form_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response: Response = requests.post(
        f"https://{hostname}.com/api/access/v1/oauth/token",
        files=form_data,
    )
    res_body: OneTrustOAuthResponse = response.json()
    return res_body.access_token
