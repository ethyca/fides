from __future__ import annotations

from typing import IO, Any, Dict, Optional, Union

from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError, ParamValidationError
from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.schemas.storage.storage import StorageSecrets
from fides.api.util.aws_util import get_s3_client
from fides.config import CONFIG


def create_presigned_url_for_s3(
    s3_client: Any, bucket_name: str, file_key: str
) -> AnyHttpUrlString:
    """ "Generate a presigned URL to share an S3 object

    :param s3_client: s3 base client
    :param bucket_name: string
    :param file_key: string
    :return: Presigned URL as string.
    """
    response = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": file_key},
        ExpiresIn=CONFIG.security.subject_request_download_link_ttl_seconds,
    )

    # The response contains the presigned URL
    return response


def generic_upload_to_s3(  # pylint: disable=R0913
    storage_secrets: Dict[StorageSecrets, Any],
    bucket_name: str,
    file_key: str,
    auth_method: str,
    document: IO,
) -> Optional[AnyHttpUrlString]:
    """
    Uploads arbitrary data to S3 returned from an access request.
    Handles both small and large uploads.
    """
    logger.info("Starting S3 Upload of {}", file_key)

    try:
        s3_client = get_s3_client(auth_method, storage_secrets)

        # Define a transfer configuration for multipart uploads
        transfer_config = TransferConfig(
            multipart_threshold=5 * 1024 * 1024,  # 5 MB threshold for multipart uploads
            multipart_chunksize=5 * 1024 * 1024,  # 5 MB chunk size
        )

        # Use upload_fileobj for efficient uploads (handles both small and large files)
        s3_client.upload_fileobj(
            Fileobj=document,
            Bucket=bucket_name,
            Key=file_key,
            Config=transfer_config,
        )
        logger.info("S3 Upload of {} completed successfully", file_key)

        # Generate a presigned URL for the uploaded file
        presigned_url: AnyHttpUrlString = create_presigned_url_for_s3(
            s3_client, bucket_name, file_key
        )

        return presigned_url
    except ClientError as e:
        logger.error(
            "Encountered error while uploading and generating link for S3 object: {}", e
        )
        raise e
    except ParamValidationError as e:
        raise ValueError(f"The parameters you provided are incorrect: {e}")


def generic_download_from_s3(
    storage_secrets: Dict[StorageSecrets, Any],
    bucket_name: str,
    file_key: str,
    auth_method: str,
) -> Optional[AnyHttpUrlString]:
    """
    Generates a presigned URL for downloading an S3 object.

    :param storage_secrets: S3 storage secrets
    :param bucket_name: Name of the S3 bucket
    :param file_key: Key of the file in the bucket
    :param auth_method: Authentication method for S3
    :return: A presigned URL (str) for the S3 object
    """
    logger.info("Generating presigned URL for downloading file: {}", file_key)

    try:
        s3_client = get_s3_client(auth_method, storage_secrets)

        # Generate a presigned URL for the file
        presigned_url = create_presigned_url_for_s3(s3_client, bucket_name, file_key)
        return presigned_url

    except (ClientError, ParamValidationError) as e:
        logger.error("Failed to generate presigned URL for S3 object: {}", e)
        return None


def generic_retrieve_from_s3(
    storage_secrets: Dict[StorageSecrets, Any],
    bucket_name: str,
    file_key: str,
    auth_method: str,
    size_threshold: int = 5 * 1024 * 1024,  # 5 MB threshold
) -> Union[IO, AnyHttpUrlString]:
    """
    Retrieves arbitrary data from S3. Returns the file contents if the file is small,
    or a presigned URL to download the file if it is large.

    :param storage_secrets: S3 storage secrets
    :param bucket_name: Name of the S3 bucket
    :param file_key: Key of the file in the bucket
    :param auth_method: Authentication method for S3
    :param size_threshold: Size threshold in bytes to determine small vs large files
    :return: File contents (IO) for small files or a presigned URL (str) for large files
    """
    logger.info("Starting S3 Retrieve of {}", file_key)

    try:
        s3_client = get_s3_client(auth_method, storage_secrets)
        try:
            # Get the object metadata to check its size
            head_response = s3_client.head_object(Bucket=bucket_name, Key=file_key)
            file_size = head_response["ContentLength"]

            if file_size <= size_threshold:
                # File is small, return its contents
                response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
                return response["Body"].read()

            # File is large, return a presigned URL
            return create_presigned_url_for_s3(s3_client, bucket_name, file_key)

        except Exception as e:
            logger.error("Encountered error while retrieving S3 object: {}", e)
            raise e
    except ClientError as e:
        logger.error("Encountered error while retrieving S3 object: {}", e)
        raise e
    except ParamValidationError as e:
        raise ValueError(f"The parameters you provided are incorrect: {e}")


def generic_delete_from_s3(
    storage_secrets: Dict[StorageSecrets, Any],
    bucket_name: str,
    file_key: str,
    auth_method: str,
) -> None:
    """Deletes arbitrary data from s3"""
    logger.info("Starting S3 Delete of {}", file_key)

    try:
        s3_client = get_s3_client(auth_method, storage_secrets)
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=file_key)
        except Exception as e:
            logger.error("Encountered error while deleting s3 object: {}", e)
            raise e
    except ClientError as e:
        logger.error("Encountered error while deleting s3 object: {}", e)
        raise e
    except ParamValidationError as e:
        raise ValueError(f"The parameters you provided are incorrect: {e}")
