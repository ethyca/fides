from __future__ import annotations

from io import BytesIO
from typing import IO, Any, Dict, Optional, Tuple, Union

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
    s3_client: Any, bucket_name: str, file_key: str, ttl_seconds: Optional[int] = None
) -> AnyHttpUrlString:
    """
    Generates a presigned URL to share an S3 object

    :param s3_client: s3 base client
    :param bucket_name: string
    :param file_key: string
    :return: Presigned URL as string.
    """
    params = {"Bucket": bucket_name, "Key": file_key}
    if ttl_seconds:
        if ttl_seconds > 604800:
            raise ValueError("TTL must be less than 7 days")
        expires_in = ttl_seconds
    else:
        expires_in = CONFIG.security.subject_request_download_link_ttl_seconds
    response = s3_client.generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=expires_in,
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
    size_threshold: int = LARGE_FILE_THRESHOLD,  # 25 MB threshold
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
    get_content: bool = False,
    ttl_seconds: Optional[int] = None,
) -> Tuple[int, Union[str, IO[bytes]]]:
    """
    Retrieves a file from S3 and returns its size and either a presigned URL or the actual content.

    Args:
        storage_secrets: Dictionary containing S3 credentials
        bucket_name: Name of the S3 bucket
        file_key: Key of the file in the bucket
        auth_method: Authentication method to use
        get_content: If True, returns the actual content instead of a presigned URL

    Returns:
        Tuple containing (file_size, presigned_url_or_content)
    """
    logger.info("Retrieving S3 object: {}", file_key)
    s3_client = get_s3_client(auth_method, storage_secrets)

    try:
        # Get file size using head_object
        size_response = s3_client.head_object(Bucket=bucket_name, Key=file_key)
        # If the file is less than 25MB, we can get the content otherwise return the presigned URL
        if get_content and size_response["ContentLength"] <= LARGE_FILE_THRESHOLD:
            # Get the actual content using download_fileobj
            file_obj = BytesIO()
            s3_client.download_fileobj(
                Bucket=bucket_name, Key=file_key, Fileobj=file_obj
            )
            file_obj.seek(0)  # Reset file pointer to beginning
            return int(size_response["ContentLength"]), file_obj

        # Get presigned URL
        presigned_url = create_presigned_url_for_s3(
            s3_client, bucket_name, file_key, ttl_seconds
        )
        return int(size_response["ContentLength"]), str(presigned_url)
    except ClientError as e:
        logger.error(f"Error retrieving file from S3: {e}")
        raise e


def generic_delete_from_s3(
    storage_secrets: Dict[StorageSecrets, Any],
    bucket_name: str,
    file_key: str,
    auth_method: str,
) -> None:
    """
    Deletes arbitrary data from s3. If file_key ends with a filename, deletes just that file.
    If file_key ends with a '/', deletes all objects with that prefix.

    :param storage_secrets: S3 storage secrets
    :param bucket_name: Name of the S3 bucket
    :param file_key: Key of the file in the bucket
    :param auth_method: Authentication method for S3
    """
    logger.info("Starting S3 Delete of {}", file_key)

    s3_client = maybe_get_s3_client(auth_method, storage_secrets)
    try:
        # If the file_key ends with a '/', it's a folder prefix
        if file_key.endswith("/"):
            # List all objects with the prefix, handling pagination
            paginator = s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket_name, Prefix=file_key):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
            return

        # Delete single object
        s3_client.delete_object(Bucket=bucket_name, Key=file_key)
    except Exception as e:
        logger.error("Encountered error while deleting s3 object: {}", e)
        raise e
