from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Optional

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
    document: BytesIO,
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

        try:
            # Check if the document is a file-like object or raw bytes
            if isinstance(document, bytes):
                document = BytesIO(document)  # Wrap raw bytes in a file-like object

            # Use upload_fileobj for efficient uploads (handles both small and large files)
            s3_client.upload_fileobj(
                Fileobj=document,
                Bucket=bucket_name,
                Key=file_key,
                Config=transfer_config,
            )
        except Exception as e:
            logger.error("Encountered error while uploading S3 object: {}", e)
            raise e

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


def generic_retrieve_from_s3(
    storage_secrets: Dict[StorageSecrets, Any],
    bucket_name: str,
    file_key: str,
    auth_method: str,
) -> Optional[BytesIO]:
    """Retrieves arbitrary data from s3"""
    logger.info("Starting S3 Retrieve of {}", file_key)

    try:
        s3_client = get_s3_client(auth_method, storage_secrets)
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            return response["Body"].read()
        except Exception as e:
            logger.error("Encountered error while retrieving s3 object: {}", e)
            raise e
    except ClientError as e:
        logger.error("Encountered error while retrieving s3 object: {}", e)
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
