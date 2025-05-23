from __future__ import annotations

import json
import secrets
import zipfile
from io import BytesIO
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import pandas as pd
from botocore.exceptions import ClientError, ParamValidationError
from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.cryptography.cryptographic_util import bytes_to_b64_str
from fides.api.schemas.storage.storage import ResponseFormat, StorageSecrets
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DsrReportBuilder,
)
from fides.api.service.storage.gcs import get_gcs_client
from fides.api.service.storage.s3 import (
    create_presigned_url_for_s3,
    generic_upload_to_s3,
)
from fides.api.service.storage.util import (
    LOCAL_FIDES_UPLOAD_DIRECTORY,
    get_local_filename,
)
from fides.api.util.aws_util import get_s3_client
from fides.api.util.cache import get_cache, get_encryption_cache_key
from fides.api.util.encryption.aes_gcm_encryption_scheme import (
    encrypt_to_bytes_verify_secrets_length,
)
from fides.api.util.storage_util import StorageJSONEncoder
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


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
    resp_format: str, data: Dict[str, Any], privacy_request: PrivacyRequest
) -> BytesIO:
    """Write JSON/CSV data to in-memory file-like object to be passed to S3 or GCS. Encrypt data if encryption key/nonce
    has been cached for the given privacy request id

    :param resp_format: str, should be one of ResponseFormat
    :param data: Dict
    :param request_id: str, The privacy request id
    """
    logger.debug("Writing data to in-memory buffer")

    if resp_format == ResponseFormat.json.value:
        json_str = json.dumps(data, indent=2, default=StorageJSONEncoder().default)
        return BytesIO(
            encrypt_access_request_results(json_str, privacy_request.id).encode(
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
                    encrypt_access_request_results(
                        buffer.getvalue(), privacy_request.id
                    ),
                )

        zipped_csvs.seek(0)
        return zipped_csvs

    if resp_format == ResponseFormat.html.value:
        return DsrReportBuilder(
            privacy_request=privacy_request,
            dsr_data=data,
        ).generate()

    raise NotImplementedError(f"No handling for response format {resp_format}.")


def upload_to_s3(  # pylint: disable=R0913
    storage_secrets: Dict[StorageSecrets, Any],
    data: Dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    privacy_request: Optional[PrivacyRequest],
    document: Optional[BytesIO],
    auth_method: str,
) -> Optional[AnyHttpUrlString]:
    """Uploads arbitrary data to s3 returned from an access request"""
    logger.info("Starting S3 Upload of {}", file_key)

    if privacy_request is None and document is not None:
        _, response = generic_upload_to_s3(
            storage_secrets, bucket_name, file_key, auth_method, document
        )
        return response

    if privacy_request is None:
        raise ValueError("Privacy request must be provided")

    try:
        s3_client = get_s3_client(
            auth_method,
            storage_secrets,
            assume_role_arn=CONFIG.credentials.get(  # pylint: disable=no-member
                "storage", {}
            ).get("aws_s3_assume_role_arn"),
        )

        # handles file chunking
        try:
            s3_client.upload_fileobj(
                Fileobj=write_to_in_memory_buffer(resp_format, data, privacy_request),
                Bucket=bucket_name,
                Key=file_key,
            )
        except Exception as e:
            logger.error("Encountered error while uploading s3 object: {}", e)
            raise e

        presigned_url: AnyHttpUrlString = create_presigned_url_for_s3(
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


def upload_to_gcs(
    storage_secrets: Dict,
    data: Dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    privacy_request: PrivacyRequest,
    auth_method: str,
) -> str:
    """Uploads access request data to a Google Cloud Storage bucket"""
    logger.info("Starting Google Cloud Storage upload of {}", file_key)

    try:
        storage_client = get_gcs_client(auth_method, storage_secrets)
        bucket = storage_client.bucket(bucket_name)

        blob = bucket.blob(file_key)
        in_memory_file = write_to_in_memory_buffer(resp_format, data, privacy_request)
        content_type = {
            ResponseFormat.json.value: "application/json",
            ResponseFormat.csv.value: "application/zip",
            ResponseFormat.html.value: "application/zip",
        }
        blob.upload_from_string(
            in_memory_file.getvalue(), content_type=content_type[resp_format]
        )

        logger.info("File {} uploaded to {}", file_key, blob.public_url)

        presigned_url = blob.generate_signed_url(
            version="v4",
            expiration=CONFIG.security.subject_request_download_link_ttl_seconds,
            method="GET",
        )
        return presigned_url
    except Exception as e:
        logger.error(
            "Encountered error while uploading and generating link for Google Cloud Storage object: {}",
            e,
        )
        raise e


def upload_to_local(
    data: Dict,
    file_key: str,
    privacy_request: PrivacyRequest,
    resp_format: str = ResponseFormat.json.value,
) -> str:
    """Uploads access request data to a local folder - for testing/demo purposes only"""
    get_local_filename(file_key)

    filename = f"{LOCAL_FIDES_UPLOAD_DIRECTORY}/{file_key}"
    in_memory_file = write_to_in_memory_buffer(resp_format, data, privacy_request)

    with open(filename, "wb") as file:
        file.write(in_memory_file.getvalue())

    return "your local fides_uploads folder"
