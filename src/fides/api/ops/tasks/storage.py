from __future__ import annotations

import json
import os
import secrets
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Union

import pandas as pd
from boto3 import Session
from botocore.exceptions import ClientError, ParamValidationError
from loguru import logger

from fides.api.ops.schemas.storage.storage import (
    ResponseFormat,
    S3AuthMethod,
    StorageSecrets,
)
from fides.api.ops.util.cache import get_cache, get_encryption_cache_key
from fides.api.ops.util.encryption.aes_gcm_encryption_scheme import (
    encrypt_to_bytes_verify_secrets_length,
)
from fides.api.ops.util.storage_authenticator import get_s3_session
from fides.core.config import get_config
from fides.lib.cryptography.cryptographic_util import bytes_to_b64_str

CONFIG = get_config()
LOCAL_FIDES_UPLOAD_DIRECTORY = "fides_uploads"


def encrypt_access_request_results(data: Union[str, bytes], request_id: str) -> str:
    """Encrypt data with encryption key if provided, otherwise return unencrypted data"""
    cache = get_cache()
    encryption_cache_key = get_encryption_cache_key(
        privacy_request_id=request_id,
        encryption_attr="key",
    )
    if isinstance(data, bytes):
        data = data.decode(CONFIG.security.encoding)

    encryption_key: str | None = cache.get(encryption_cache_key)
    if not encryption_key:
        return data

    bytes_encryption_key: bytes = encryption_key.encode(
        encoding=CONFIG.security.encoding
    )
    nonce: bytes = secrets.token_bytes(CONFIG.security.aes_gcm_nonce_length)
    # b64encode the entire nonce and the encrypted message together
    return bytes_to_b64_str(
        nonce
        + encrypt_to_bytes_verify_secrets_length(data, bytes_encryption_key, nonce)
    )


def write_to_in_memory_buffer(
    resp_format: str, data: Dict[str, Any], request_id: str
) -> BytesIO:
    """Write JSON/CSV data to in-memory file-like object to be passed to S3. Encrypt data if encryption key/nonce
    has been cached for the given privacy request id

    :param resp_format: str, should be one of ResponseFormat
    :param data: Dict
    :param request_id: str, The privacy request id
    """
    logger.info("Writing data to in-memory buffer")

    if resp_format == ResponseFormat.json.value:
        json_str = json.dumps(data, indent=2, default=_handle_json_encoding)
        return BytesIO(
            encrypt_access_request_results(json_str, request_id).encode(
                CONFIG.security.encoding
            )
        )

    if resp_format == ResponseFormat.csv.value:
        zipped_csvs = BytesIO()
        with zipfile.ZipFile(zipped_csvs, "w") as f:
            for key in data:
                df = pd.json_normalize(data[key])
                buffer = BytesIO()
                df.to_csv(buffer, index=False, encoding=CONFIG.security.encoding)
                buffer.seek(0)
                f.writestr(
                    f"{key}.csv",
                    encrypt_access_request_results(buffer.getvalue(), request_id),
                )

        zipped_csvs.seek(0)
        return zipped_csvs

    raise NotImplementedError(f"No handling for response format {resp_format}.")


def create_presigned_url_for_s3(
    s3_client: Session, bucket_name: str, object_name: str
) -> str:
    """ "Generate a presigned URL to share an S3 object

    :param s3_client: s3 base client
    :param bucket_name: string
    :param object_name: string
    :return: Presigned URL as string.
    """
    response = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": object_name},
        ExpiresIn=CONFIG.security.subject_request_download_link_ttl_seconds,
    )

    # The response contains the presigned URL
    return response


def upload_to_s3(  # pylint: disable=R0913
    storage_secrets: Dict[StorageSecrets, Any],
    data: Dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    request_id: str,
    auth_method: S3AuthMethod,
) -> str:
    """Uploads arbitrary data to s3 returned from an access request"""
    logger.info("Starting S3 Upload of {}", file_key)

    try:
        my_session = get_s3_session(auth_method, storage_secrets)
        s3_client = my_session.client("s3")

        # handles file chunking
        try:
            s3_client.upload_fileobj(
                Fileobj=write_to_in_memory_buffer(resp_format, data, request_id),
                Bucket=bucket_name,
                Key=file_key,
            )
        except Exception as e:
            logger.error("Encountered error while uploading s3 object: {}", e)
            raise e

        presigned_url: str = create_presigned_url_for_s3(
            s3_client, bucket_name, file_key
        )

        return presigned_url
    except ClientError as e:
        logger.error(
            "Encountered error while uploading and generating link for s3 object: {}", e
        )
        raise e
    except ParamValidationError as e:
        raise ValueError(f"The parameters you provided are incorrect: {e}")


def _handle_json_encoding(field: Any) -> str:
    """Specify str format for datetime objects"""
    if isinstance(field, datetime):
        return field.strftime("%Y-%m-%dT%H:%M:%S")
    return field


def upload_to_local(payload: Dict, file_key: str, request_id: str) -> str:
    """Uploads access request data to a local folder - for testing/demo purposes only"""
    if not os.path.exists(LOCAL_FIDES_UPLOAD_DIRECTORY):
        os.makedirs(LOCAL_FIDES_UPLOAD_DIRECTORY)

    filename = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{file_key}"
    data_str: str = encrypt_access_request_results(
        json.dumps(payload, default=_handle_json_encoding), request_id
    )
    with open(filename, "w") as file:  # pylint: disable=W1514
        file.write(data_str)

    return "your local fides_uploads folder"
