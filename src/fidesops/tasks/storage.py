import json
import logging
import os
import secrets
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Union

import pandas as pd
import requests
from botocore.exceptions import ClientError, ParamValidationError

from fidesops.core.config import config
from fidesops.models.storage import ResponseFormat
from fidesops.schemas.storage.storage import StorageSecrets
from fidesops.util.cache import get_cache, get_encryption_cache_key
from fidesops.util.cryptographic_util import bytes_to_b64_str
from fidesops.util.encryption.aes_gcm_encryption_scheme import (
    encrypt_to_bytes_verify_secrets_length,
)
from fidesops.util.storage_authenticator import (
    get_onetrust_access_token,
    get_s3_session,
)

logger = logging.getLogger(__name__)


LOCAL_FIDES_UPLOAD_DIRECTORY = "fides_uploads"


def encrypt_access_request_results(data: Union[str, bytes], request_id: str) -> str:
    """Encrypt data with encryption key if provided, otherwise return unencrypted data"""
    cache = get_cache()
    encryption_cache_key = get_encryption_cache_key(
        privacy_request_id=request_id,
        encryption_attr="key",
    )
    if isinstance(data, bytes):
        data = data.decode(config.security.ENCODING)

    encryption_key: str = cache.get(encryption_cache_key)
    if not encryption_key:
        return data

    bytes_encryption_key: bytes = encryption_key.encode(
        encoding=config.security.ENCODING
    )
    nonce: bytes = secrets.token_bytes(config.security.AES_GCM_NONCE_LENGTH)
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
                config.security.ENCODING
            )
        )

    if resp_format == ResponseFormat.csv.value:
        zipped_csvs = BytesIO()
        with zipfile.ZipFile(zipped_csvs, "w") as f:
            for key in data:
                df = pd.json_normalize(data[key])
                buffer = BytesIO()
                df.to_csv(buffer, index=False, encoding=config.security.ENCODING)
                buffer.seek(0)
                f.writestr(
                    f"{key}.csv",
                    encrypt_access_request_results(buffer.getvalue(), request_id),
                )

        zipped_csvs.seek(0)
        return zipped_csvs

    raise NotImplementedError(f"No handling for response format {resp_format}.")


def upload_to_s3(  # pylint: disable=R0913
    storage_secrets: Dict[StorageSecrets, Any],
    data: Dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    request_id: str,
) -> str:
    """Uploads arbitrary data to s3 returned from an access request"""
    logger.info(f"Starting S3 Upload of {file_key}")
    try:
        my_session = get_s3_session(
            aws_access_key_id=storage_secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value],
            aws_secret_access_key=storage_secrets[
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value
            ],
        )

        s3 = my_session.client("s3")

        # handles file chunking
        s3.upload_fileobj(
            Fileobj=write_to_in_memory_buffer(resp_format, data, request_id),
            Bucket=bucket_name,
            Key=file_key,
        )
        # todo- move to outbound_urn_registry
        return "https://%s.s3.amazonaws.com/%s" % (bucket_name, file_key)
    except ClientError as e:
        raise e
    except ParamValidationError as e:
        raise ValueError(f"The parameters you provided are incorrect: {e}")


def upload_to_onetrust(
    payload: Dict,
    storage_secrets: Dict[StorageSecrets, Any],
    ref_id: str,
) -> str:
    """Uploads arbitrary data to onetrust returned from an access request"""
    logger.info(f"Starting OneTrust Upload for ref_id {ref_id}")

    onetrust_hostname = storage_secrets[StorageSecrets.ONETRUST_HOSTNAME.value]
    access_token = get_onetrust_access_token(
        client_id=storage_secrets[StorageSecrets.ONETRUST_CLIENT_ID.value],
        client_secret=storage_secrets[StorageSecrets.ONETRUST_CLIENT_SECRET.value],
        hostname=onetrust_hostname,
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    requests.post(
        # todo- move to outbound_urn_registry
        f"https://{onetrust_hostname}.com/api/datasubject/v3/datadiscovery/requestqueues/{ref_id}",
        data=payload,
        headers=headers,
    )
    return "success"


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
    with open(filename, "w") as file:
        file.write(data_str)

    return "success"
