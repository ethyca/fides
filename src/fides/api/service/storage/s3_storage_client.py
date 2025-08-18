from __future__ import annotations

from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError
from loguru import logger

from fides.api.service.storage.cloud_storage_client import (
    CloudStorageClient,
    MultipartUploadResponse,
    UploadPartResponse,
)
from fides.api.util.aws_util import get_s3_client


class S3StorageClient(CloudStorageClient):
    """S3-specific implementation of CloudStorageClient"""

    def __init__(self, s3_client: Any):
        self.client = s3_client

    def create_multipart_upload(
        self,
        bucket: str,
        key: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> MultipartUploadResponse:
        """Initiate S3 multipart upload"""
        try:
            params = {
                'Bucket': bucket,
                'Key': key,
                'ContentType': content_type
            }
            if metadata:
                params['Metadata'] = metadata

            response = self.client.create_multipart_upload(**params)
            return MultipartUploadResponse(
                upload_id=response['UploadId'],
                metadata=response
            )
        except ClientError as e:
            logger.error("Failed to create multipart upload: {}", e)
            raise

    def upload_part(
        self,
        bucket: str,
        upload_id: str,
        part_number: int,
        body: bytes,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadPartResponse:
        """Upload a part to S3 multipart upload"""
        try:
            response = self.client.upload_part(
                Bucket=bucket,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=body
            )
            return UploadPartResponse(
                etag=response['ETag'],
                part_number=part_number,
                metadata=response
            )
        except ClientError as e:
            logger.error("Failed to upload part {}: {}", part_number, e)
            raise

    def complete_multipart_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: List[UploadPartResponse],
        metadata: Optional[Dict[str, str]] = None
    ) -> None:
        """Complete S3 multipart upload"""
        try:
            # Convert our parts to S3 format
            s3_parts = [
                {'ETag': part.etag, 'PartNumber': part.part_number}
                for part in parts
            ]

            self.client.complete_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={'Parts': s3_parts}
            )
        except ClientError as e:
            logger.error("Failed to complete multipart upload: {}", e)
            raise

    def abort_multipart_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str
    ) -> None:
        """Abort S3 multipart upload"""
        try:
            self.client.abort_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id
            )
        except ClientError as e:
            logger.warning("Failed to abort multipart upload: {}", e)
            # Don't raise here as this is cleanup

    def get_object_head(
        self,
        bucket: str,
        key: str
    ) -> Dict[str, Any]:
        """Get S3 object metadata"""
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            return response
        except ClientError as e:
            logger.error("Failed to get object head: {}", e)
            raise

    def get_object_range(
        self,
        bucket: str,
        key: str,
        start_byte: int,
        end_byte: int
    ) -> bytes:
        """Get a range of bytes from S3 object"""
        try:
            response = self.client.get_object(
                Bucket=bucket,
                Key=key,
                Range=f'bytes={start_byte}-{end_byte}'
            )
            data = response['Body'].read()
            response['Body'].close()
            return data
        except ClientError as e:
            logger.error("Failed to get object range: {}", e)
            raise

    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        ttl_seconds: Optional[int] = None
    ) -> str:
        """Generate S3 presigned URL"""
        try:
            from fides.api.service.storage.s3 import create_presigned_url_for_s3
            return create_presigned_url_for_s3(
                self.client, bucket, key, ttl_seconds
            )
        except Exception as e:
            logger.error("Failed to generate presigned URL: {}", e)
            raise


def create_s3_storage_client(
    auth_method: str,
    storage_secrets: Dict[str, Any]
) -> S3StorageClient:
    """Factory function to create an S3 storage client"""
    s3_client = get_s3_client(auth_method, storage_secrets)
    return S3StorageClient(s3_client)
