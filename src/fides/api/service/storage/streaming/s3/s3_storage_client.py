from __future__ import annotations

from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError
from loguru import logger

from fides.api.service.storage.s3 import create_presigned_url_for_s3
from fides.api.service.storage.streaming.cloud_storage_client import (
    CloudStorageClient,
    MultipartUploadResponse,
    UploadPartResponse,
)
from fides.api.service.storage.streaming.s3.s3_schemas import (
    AWSAbortMultipartUploadRequest,
    AWSCompleteMultipartUploadRequest,
    AWSCreateMultipartUploadRequest,
    AWSGeneratePresignedUrlRequest,
    AWSGetObjectRangeRequest,
    AWSGetObjectRequest,
    AWSUploadPartRequest,
)
from fides.api.service.storage.streaming.schemas import UploadPartResponse
from fides.api.util.aws_util import get_s3_client


class S3StorageClient(CloudStorageClient):
    """S3-specific implementation of CloudStorageClient for multipart uploads and object operations.

    This client handles S3 multipart uploads, object metadata retrieval, and presigned URL generation.
    It's used by the streaming storage system to enable memory-efficient processing of large files.
    """

    def __init__(self, s3_client: Any):
        """Initialize S3StorageClient with an S3 client.

        Args:
            s3_client: Boto3 S3 client instance for AWS operations
        """
        self.client = s3_client

    def create_multipart_upload(
        self,
        bucket: str,
        key: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> MultipartUploadResponse:
        """Initiate S3 multipart upload for large file processing.

        This method starts a multipart upload session in S3, which allows large files to be
        uploaded in smaller parts. This is essential for the streaming storage system to
        handle large datasets without loading entire files into memory.

        Args:
            bucket: S3 bucket name where the file will be stored
            key: S3 object key (file path) within the bucket
            content_type: MIME type of the file being uploaded (e.g., "application/zip")
            metadata: Optional key-value pairs to store as object metadata

        Returns:
            MultipartUploadResponse containing the upload_id and full S3 response metadata

        Raises:
            ClientError: If S3 operations fail (e.g., bucket doesn't exist, permissions denied)
            ValueError: If parameters fail validation (empty/whitespace strings for bucket/key/content_type)
        """
        # Validate parameters using Pydantic schema
        request = AWSCreateMultipartUploadRequest(
            bucket=bucket,
            key=key,
            content_type=content_type,
            metadata=metadata,
        )

        try:
            params = {
                "Bucket": request.bucket,
                "Key": request.key,
                "ContentType": request.content_type,
            }
            if request.metadata:
                params["Metadata"] = request.metadata

            response = self.client.create_multipart_upload(**params)
            return MultipartUploadResponse(
                upload_id=response["UploadId"], metadata=response
            )
        except ClientError as e:
            logger.error("Failed to create multipart upload: {}", e)
            raise

    def upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        body: bytes,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadPartResponse:
        """Upload a part to an existing S3 multipart upload.

        This method uploads a single part of a multipart upload. Parts are numbered
        sequentially starting from 1. The streaming storage system uses this to upload
        file chunks incrementally, maintaining low memory usage.

        Args:
            bucket: S3 bucket name where the multipart upload was initiated
            key: S3 object key (file path) for the multipart upload
            upload_id: Upload ID returned from create_multipart_upload
            part_number: Sequential part number (1, 2, 3, etc.)
            body: Binary data content for this part
            metadata: Optional metadata for this specific part (rarely used)

        Returns:
            UploadPartResponse containing the ETag, part number, and S3 response metadata

        Raises:
            ClientError: If S3 operations fail (e.g., invalid upload_id, part number out of order)
            ValueError: If parameters fail validation (empty/whitespace strings, invalid part numbers, etc.)
        """
        # Validate parameters using Pydantic schema
        request = AWSUploadPartRequest(
            bucket=bucket,
            key=key,
            upload_id=upload_id,
            part_number=part_number,
            body=body,
            metadata=metadata,
        )

        try:
            response = self.client.upload_part(
                Bucket=request.bucket,
                Key=request.key,
                PartNumber=request.part_number,
                UploadId=request.upload_id,
                Body=request.body,
            )
            return UploadPartResponse(
                etag=response["ETag"],
                part_number=request.part_number,
                metadata=response,
            )
        except ClientError as e:
            logger.error("Failed to upload part {}: {}", request.part_number, e)
            raise

    def complete_multipart_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: List[UploadPartResponse],
        metadata: Optional[
            Dict[str, str]
        ] = None,  # matches CloudStorageClient abstract method
    ) -> None:
        """Complete an S3 multipart upload by combining all uploaded parts.

        This method finalizes a multipart upload by combining all uploaded parts into
        a single S3 object. The parts must be provided in order, and S3 will validate
        that all parts are present and properly uploaded.

        Args:
            bucket: S3 bucket name where the multipart upload was initiated
            key: S3 object key (file path) for the final object
            upload_id: Upload ID returned from create_multipart_upload
            parts: List of UploadPartResponse objects in sequential order
            metadata: Optional metadata to apply to the final object

        Raises:
            ClientError: If S3 operations fail (e.g., parts missing, upload already completed)
            ValueError: If parameters fail validation (empty/whitespace strings for bucket/key/upload_id, invalid parts list)

        """
        # Validate parameters using Pydantic schema
        request = AWSCompleteMultipartUploadRequest(
            bucket=bucket,
            key=key,
            upload_id=upload_id,
            parts=parts,
            metadata=metadata,
        )

        try:
            # Convert our parts to S3 format
            s3_parts = [
                {"ETag": part.etag, "PartNumber": part.part_number}
                for part in request.parts
            ]

            self.client.complete_multipart_upload(
                Bucket=request.bucket,
                Key=request.key,
                UploadId=request.upload_id,
                MultipartUpload={"Parts": s3_parts},
            )
        except ClientError as e:
            logger.error("Failed to complete multipart upload: {}", e)
            raise

    def abort_multipart_upload(self, bucket: str, key: str, upload_id: str) -> None:
        """Abort an existing S3 multipart upload.

        This method cancels an in-progress multipart upload and removes any uploaded parts.
        It's used when uploads fail or need to be cancelled.

        Args:
            bucket: S3 bucket name where the multipart upload was initiated
            key: S3 object key (file path) for the multipart upload
            upload_id: Upload ID returned from create_multipart_upload

        Raises:
            ClientError: If S3 operations fail (e.g., upload already completed)
            ValueError: If parameters fail validation (empty/whitespace strings for bucket/key/upload_id)

        """
        # Validate parameters using Pydantic schema
        request = AWSAbortMultipartUploadRequest(
            bucket=bucket,
            key=key,
            upload_id=upload_id,
        )

        try:
            self.client.abort_multipart_upload(
                Bucket=request.bucket, Key=request.key, UploadId=request.upload_id
            )
        except ClientError as e:
            logger.error("Failed to abort multipart upload: {}", e)
            raise

    def get_object_head(self, bucket: str, key: str) -> Dict[str, Any]:
        """Get S3 object metadata without downloading the object content.

        This method retrieves object metadata (including size, content type, etc.)
        without downloading the actual file content. The streaming storage system
        uses this to determine file sizes for chunking and progress tracking.

        Args:
            bucket: S3 bucket name containing the object
            key: S3 object key (file path) within the bucket

        Returns:
            Dictionary containing object metadata including:
            - ContentLength: File size in bytes
            - ContentType: MIME type of the object
            - LastModified: Timestamp of last modification
            - ETag: Object's ETag for validation
            - Additional S3 metadata fields

        Raises:
            ClientError: If S3 operations fail (e.g., object not found, permissions denied)
            ValueError: If parameters fail validation (empty/whitespace strings for bucket/key)

        """
        # Validate parameters using Pydantic schema
        request = AWSGetObjectRequest(bucket=bucket, key=key)

        try:
            response = self.client.head_object(Bucket=request.bucket, Key=request.key)
            return response
        except ClientError as e:
            logger.error("Failed to get object head: {}", e)
            raise

    def get_object_range(
        self, bucket: str, key: str, start_byte: int, end_byte: int
    ) -> bytes:
        """Get a specific byte range from an S3 object.

        This method downloads only a portion of an S3 object, specified by byte range.
        It's essential for the streaming storage system to process large files in
        small chunks without loading entire files into memory.

        Args:
            bucket: S3 bucket name containing the object
            key: S3 object key (file path) within the bucket
            start_byte: Starting byte position (inclusive, 0-based)
            end_byte: Ending byte position (inclusive, 0-based)

        Returns:
            Bytes object containing the requested byte range

        Raises:
            ClientError: If S3 operations fail (e.g., object not found, invalid range)
            ValueError: If parameters fail validation (empty/whitespace strings for bucket/key, invalid byte ranges)
        """
        # Validate parameters using Pydantic schema
        request = AWSGetObjectRangeRequest(
            bucket=bucket,
            key=key,
            start_byte=start_byte,
            end_byte=end_byte,
        )

        try:
            response = self.client.get_object(
                Bucket=request.bucket,
                Key=request.key,
                Range=f"bytes={request.start_byte}-{request.end_byte}",
            )
            data = response["Body"].read()
            response["Body"].close()
            return data
        except ClientError as e:
            logger.error("Failed to get object range: {}", e)
            raise

    def generate_presigned_url(
        self, bucket: str, key: str, ttl_seconds: Optional[int] = None
    ) -> str:
        """Generate a presigned URL for secure, time-limited access to an S3 object.

        This method creates a presigned URL that allows temporary access to an S3 object
        without requiring AWS credentials. The streaming storage system uses this to
        provide download links for processed files.

        Args:
            bucket: S3 bucket name containing the object
            key: S3 object key (file path) within the bucket
            ttl_seconds: Optional TTL in seconds (max 7 days, defaults to config value)

        Returns:
            Presigned URL string that can be used to download the object

        Raises:
            ValueError: If TTL exceeds 7 days (S3 limit) or parameters fail validation (empty/whitespace strings for bucket/key)
            Exception: If URL generation fails (e.g., object not found, permissions denied)
        """
        # Validate parameters using Pydantic schema
        request = AWSGeneratePresignedUrlRequest(
            bucket=bucket,
            key=key,
            ttl_seconds=ttl_seconds,
        )

        try:
            return create_presigned_url_for_s3(
                self.client, request.bucket, request.key, request.ttl_seconds
            )
        except Exception as e:
            logger.error("Failed to generate presigned URL: {}", e)
            raise


def create_s3_storage_client(
    auth_method: str, storage_secrets: Dict[str, Any]
) -> S3StorageClient:
    """Factory function to create an S3 storage client"""
    s3_client = get_s3_client(auth_method, storage_secrets)
    return S3StorageClient(s3_client)
