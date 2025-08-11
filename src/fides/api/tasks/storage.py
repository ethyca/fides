from __future__ import annotations

import json
import zipfile
from io import BytesIO
from typing import TYPE_CHECKING, Any, Optional

from botocore.exceptions import ClientError, ParamValidationError
from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import ResponseFormat, StorageSecrets
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DsrReportBuilder,
)
from fides.api.service.storage.gcs import get_gcs_blob
from fides.api.service.storage.s3 import (
    create_presigned_url_for_s3,
    generic_upload_to_s3,
)
from fides.api.service.storage.util import (
    LOCAL_FIDES_UPLOAD_DIRECTORY,
    get_local_filename,
)
from fides.api.tasks.csv_utils import write_csv_to_zip
from fides.api.tasks.encryption_utils import encrypt_access_request_results
from fides.api.util.aws_util import get_s3_client
from fides.api.util.storage_util import StorageJSONEncoder
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


def write_to_in_memory_buffer(
    resp_format: str, data: dict[str, Any], privacy_request: PrivacyRequest
) -> BytesIO:
    """Write JSON/CSV data to in-memory file-like object to be passed to S3 or GCS. Encrypt data if encryption key/nonce
    has been cached for the given privacy request id

    :param resp_format: str, should be one of ResponseFormat
    :param data: Dict
    :param request_id: str, The privacy request id
    """

    logger.debug("Writing data to in-memory buffer")
    try:
        if resp_format == ResponseFormat.html.value:
            return DsrReportBuilder(
                privacy_request=privacy_request,
                dsr_data=data,
            ).generate()

        if resp_format == ResponseFormat.json.value:
            return convert_dict_to_encrypted_json(data, privacy_request.id)

        if resp_format == ResponseFormat.csv.value:
            zipped_csvs = BytesIO()
            with zipfile.ZipFile(zipped_csvs, "w") as f:
                write_csv_to_zip(f, data, privacy_request.id)
            zipped_csvs.seek(0)
            return zipped_csvs
    except Exception as e:
        logger.error(f"Error writing data to in-memory buffer: {str(e)}")
        raise e

    raise NotImplementedError(f"No handling for response format {resp_format}.")


def convert_dict_to_encrypted_json(
    data: dict[str, Any], privacy_request_id: str
) -> BytesIO:
    """Convert data to JSON and encrypt it.

    Args:
        data: The data to convert and encrypt
        privacy_request_id: The ID of the privacy request for encryption

    Returns:
        BytesIO: A file-like object containing the encrypted JSON data

    Raises:
        Exception: If JSON conversion fails
    """
    try:
        json_str = json.dumps(data, indent=2, default=StorageJSONEncoder().default)
        return BytesIO(
            encrypt_access_request_results(json_str, privacy_request_id).encode(
                CONFIG.security.encoding
            )
        )
    except Exception as e:
        logger.error(f"Error converting data to JSON: {str(e)}")
        logger.error(f"Data that failed to convert: {data}")
        raise


def upload_to_s3(  # pylint: disable=R0913
    storage_secrets: dict[StorageSecrets, Any],
    data: dict,
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
        )
    except (ClientError, ParamValidationError) as e:
        logger.error(f"Error getting s3 client: {str(e)}")
        raise StorageUploadError(f"Error getting s3 client: {str(e)}")

    # handles file chunking
    try:
        s3_client.upload_fileobj(
            Fileobj=write_to_in_memory_buffer(resp_format, data, privacy_request),
            Bucket=bucket_name,
            Key=file_key,
        )
    except ClientError as e:
        logger.error("Encountered error while uploading s3 object: {}", e)
        raise StorageUploadError(f"Error uploading to S3: {e}")

    try:
        presigned_url: AnyHttpUrlString = create_presigned_url_for_s3(
            s3_client, bucket_name, file_key
        )

        return presigned_url
    except ClientError as e:
        logger.error(
            "Encountered error while uploading and generating link for s3 object: {}", e
        )
        raise StorageUploadError(f"Error uploading to S3: {e}")


def upload_to_gcs(
    storage_secrets: dict,
    data: dict,
    bucket_name: str,
    file_key: str,
    resp_format: str,
    privacy_request: PrivacyRequest,
    auth_method: str,
) -> str:
    """Uploads access request data to a Google Cloud Storage bucket"""
    logger.info("Starting Google Cloud Storage upload of {}", file_key)
    content_type = {
        ResponseFormat.json.value: "application/json",
        ResponseFormat.csv.value: "application/zip",
        ResponseFormat.html.value: "application/zip",
    }

    blob = get_gcs_blob(auth_method, storage_secrets, bucket_name, file_key)
    in_memory_file = write_to_in_memory_buffer(resp_format, data, privacy_request)

    try:
        blob.upload_from_string(
            in_memory_file.getvalue(), content_type=content_type[resp_format]
        )
    except Exception as e:
        logger.error("Error uploading to GCS: {}", str(e))
        logger.error(
            "Encountered error while uploading and generating link for Google Cloud Storage object: {}",
            e,
        )
        raise

    logger.info("File {} uploaded to {}", file_key, blob.public_url)

    try:
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
        raise StorageUploadError(f"Error uploading to Google Cloud Storage: {e}")


def upload_to_local(
    data: dict,
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
