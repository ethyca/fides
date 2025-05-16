from __future__ import annotations

from typing import IO, Any, Dict, Tuple

from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError, ParamValidationError
from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.schemas.storage.storage import StorageSecrets
from fides.api.service.storage.util import (
    LARGE_FILE_THRESHOLD,
    get_allowed_file_type_or_raise,
)
from fides.api.util.aws_util import get_s3_client
from fides.config import CONFIG


def maybe_get_s3_client(
    auth_method: str, storage_secrets: Dict[StorageSecrets, Any]
) -> Any:
    """
    Returns an S3 client if the client can be created successfully, otherwise raises an exception.
    """
    try:
        return get_s3_client(auth_method, storage_secrets)
    except ClientError as e:
        logger.error(
            "Encountered error while uploading and generating link for S3 object: {}", e
        )
        raise e
    except ParamValidationError as e:
        raise ValueError(f"The parameters you provided are incorrect: {e}")


def create_presigned_url_for_s3(
    s3_client: Any, bucket_name: str, file_key: str
) -> AnyHttpUrlString:
    """
    Generates a presigned URL to share an S3 object

    :param s3_client: s3 base client
    :param bucket_name: string
    :param file_key: string
    :return: Presigned URL as string.
    """
    params = {"Bucket": bucket_name, "Key": file_key}
    response = s3_client.generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=CONFIG.security.subject_request_download_link_ttl_seconds,
    )

    # The response contains the presigned URL
    return response


def get_file_size(s3_client: Any, bucket_name: str, file_key: str) -> int:
    """
    Returns the size of a file in bytes.
    """
    return s3_client.head_object(Bucket=bucket_name, Key=file_key)["ContentLength"]


def generic_upload_to_s3(  # pylint: disable=R0913
    storage_secrets: Dict[StorageSecrets, Any],
    bucket_name: str,
    file_key: str,
    auth_method: str,
    document: IO[bytes],
    size_threshold: int = LARGE_FILE_THRESHOLD,  # 5 MB threshold
) -> Tuple[int, AnyHttpUrlString]:
    """
    Uploads file like objects to S3.
    Handles both small and large uploads.

    :param storage_secrets: S3 storage secrets
    :param bucket_name: Name of the S3 bucket
    :param file_key: Key of the file in the bucket
    :param auth_method: Authentication method for S3
    :param document: File contents to upload
    """
    logger.info("Starting S3 Upload of {}", file_key)

    # Validate that the document is a file-like object
    if not hasattr(document, "read") or not hasattr(document, "seek"):
        raise TypeError(
            f"The 'document' parameter must be a file-like object supporting 'read' and 'seek'. "
            f"Received: {type(document)}, {document}"
        )

    # Ensure the file pointer is at the beginning
    try:
        document.seek(0)
    except Exception as e:
        raise ValueError(f"Failed to reset file pointer for document: {e}")

    s3_client = maybe_get_s3_client(auth_method, storage_secrets)

    # Define a transfer configuration for multipart uploads
    transfer_config = TransferConfig(
        multipart_threshold=size_threshold,
        multipart_chunksize=size_threshold,
    )

    # Use upload_fileobj for efficient uploads (handles both small and large files)
    try:
        file_type: str = get_allowed_file_type_or_raise(file_key)
        # Use upload_fileobj for efficient uploads (handles both small and large files)
        s3_client.upload_fileobj(
            Fileobj=document,
            Bucket=bucket_name,
            Key=file_key,
            Config=transfer_config,
            ExtraArgs={"ContentType": file_type} if file_type else {},
        )
        file_size = get_file_size(s3_client, bucket_name, file_key)
    except Exception as e:
        logger.error(f"Failed to upload file {file_key} to bucket {bucket_name}: {e}")
        raise e  # Re-raise the exception if you want it to propagate

    # Generate a presigned URL for the uploaded file
    logger.info(f"Successfully uploaded file {file_key} to bucket {bucket_name}")
    return file_size, create_presigned_url_for_s3(s3_client, bucket_name, file_key)


def generic_retrieve_from_s3(
    storage_secrets: Dict[StorageSecrets, Any],
    bucket_name: str,
    file_key: str,
    auth_method: str,
) -> Tuple[int, AnyHttpUrlString]:
    """
    Retrieves file metadata and generates a presigned URL for downloading an S3 object.

    :param storage_secrets: S3 storage secrets
    :param bucket_name: Name of the S3 bucket
    :param file_key: Key of the file in the bucket
    :param auth_method: Authentication method for S3
    :return: Tuple containing (file_size, presigned_url)
    """
    logger.info("Retrieving S3 object: {}", file_key)

    s3_client = maybe_get_s3_client(auth_method, storage_secrets)
    try:
        get_allowed_file_type_or_raise(file_key)
        file_size = get_file_size(s3_client, bucket_name, file_key)
        return file_size, create_presigned_url_for_s3(s3_client, bucket_name, file_key)
    except Exception as e:
        logger.error("Encountered error while retrieving S3 object: {}", e)
        raise e


def generic_delete_from_s3(
    storage_secrets: Dict[StorageSecrets, Any],
    bucket_name: str,
    file_key: str,
    auth_method: str,
) -> None:
    """
    Deletes arbitrary data from s3

    :param storage_secrets: S3 storage secrets
    :param bucket_name: Name of the S3 bucket
    :param file_key: Key of the file in the bucket
    :param auth_method: Authentication method for S3
    """
    logger.info("Starting S3 Delete of {}", file_key)

    s3_client = maybe_get_s3_client(auth_method, storage_secrets)
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=file_key)
    except Exception as e:
        logger.error("Encountered error while deleting s3 object: {}", e)
        raise e
