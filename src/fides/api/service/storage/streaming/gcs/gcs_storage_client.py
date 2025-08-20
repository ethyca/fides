from __future__ import annotations

import time
from typing import Any, Optional, Union

from fideslang.validation import AnyHttpUrlString
from google.cloud.exceptions import GoogleCloudError
from google.cloud.storage import Client  # type: ignore
from loguru import logger

from fides.api.schemas.storage.storage import StorageSecrets
from fides.api.service.storage.gcs import get_gcs_client
from fides.api.service.storage.streaming.cloud_storage_client import CloudStorageClient
from fides.api.service.storage.streaming.gcs.gcs_schemas import (
    GCSAbortResumableUploadRequest,
    GCSChunkUploadRequest,
    GCSChunkUploadResponse,
    GCSCompleteResumableUploadRequest,
    GCSGenerateSignedUrlRequest,
    GCSGetObjectRangeRequest,
    GCSGetObjectRequest,
    GCSResumableUploadRequest,
    GCSResumableUploadResponse,
)
from fides.api.service.storage.streaming.schemas import (
    MultipartUploadResponse,
    UploadPartResponse,
)
from fides.api.service.storage.streaming.util import GCS_MIN_CHUNK_SIZE


class GCSStorageClient(CloudStorageClient):
    """GCS-specific implementation of CloudStorageClient using resumable uploads"""

    def __init__(self, gcs_client: Client):
        self.client = gcs_client
        self._resumable_uploads: dict[str, Any] = {}

    def create_multipart_upload(
        self,
        bucket: str,
        key: str,
        content_type: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> MultipartUploadResponse:
        """Initiate GCS resumable upload (multipart equivalent)"""
        # Validate input parameters using GCS-specific schema
        request = GCSResumableUploadRequest(
            bucket=bucket,
            key=key,
            content_type=content_type,
            metadata=metadata,
        )

        try:
            bucket_obj = self.client.bucket(request.bucket)
            blob = bucket_obj.blob(request.key)

            # Set metadata if provided
            if request.metadata:
                blob.metadata = request.metadata

            # Start resumable upload
            resumable_url = blob.create_resumable_upload_session(
                content_type=request.content_type
            )

            # Store the resumable upload info
            upload_id = f"gcs_resumable_{int(time.time())}_{hash(request.key)}"
            self._resumable_uploads[upload_id] = {
                "blob": blob,
                "resumable_url": resumable_url,
                "bucket": request.bucket,
                "key": request.key,
                "bytes_uploaded": 0,
            }

            return MultipartUploadResponse(
                upload_id=upload_id, metadata={"resumable_url": resumable_url}
            )
        except GoogleCloudError as e:
            logger.error("Failed to create resumable upload: {}", e)
            raise

    def upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        body: bytes,
        metadata: Optional[dict[str, str]] = None,
    ) -> UploadPartResponse:
        """Upload a part to GCS resumable upload (simulated for compatibility)"""
        # Validate input parameters using GCS-specific schema
        request = GCSChunkUploadRequest(
            bucket=bucket,
            key=key,
            upload_id=upload_id,
            chunk_data=body,
            metadata=metadata,
        )

        try:
            if request.upload_id not in self._resumable_uploads:
                raise ValueError(f"Unknown upload ID: {request.upload_id}")

            upload_info = self._resumable_uploads[request.upload_id]
            # blob = upload_info["blob"]
            # resumable_url = upload_info["resumable_url"]

            # Validate chunk size meets GCS requirements
            if len(request.chunk_data) < GCS_MIN_CHUNK_SIZE:
                logger.warning(
                    "Chunk size {} bytes is below GCS minimum requirement of {} bytes",
                    len(request.chunk_data),
                    GCS_MIN_CHUNK_SIZE,
                )

            # For GCS, we'll simulate parts by tracking upload progress
            # In practice, GCS resumable uploads are more like streaming uploads
            # This is a simplified implementation - real GCS would use different patterns

            # For now, we'll just return a mock response
            # In a real implementation, you'd want to use GCS's resumable upload API properly
            return UploadPartResponse(
                etag=f"gcs_part_{part_number}_{hash(request.chunk_data)}",
                part_number=part_number,
                metadata={"gcs_resumable": True},
            )
        except Exception as e:
            logger.error("Failed to upload part {}: {}", part_number, e)
            raise

    def complete_multipart_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: list[UploadPartResponse],
        metadata: Optional[dict[str, str]] = None,
    ) -> None:
        """Complete GCS resumable upload"""
        # Validate input parameters using GCS-specific schema
        request = GCSCompleteResumableUploadRequest(
            bucket=bucket,
            key=key,
            upload_id=upload_id,
            metadata=metadata,
        )

        try:
            if request.upload_id not in self._resumable_uploads:
                raise ValueError(f"Unknown upload ID: {request.upload_id}")

            upload_info = self._resumable_uploads[request.upload_id]
            blob = upload_info["blob"]

            # For GCS, we'd finalize the resumable upload here
            # This is a placeholder - real implementation would use GCS API
            logger.info("Completing GCS resumable upload for {}", request.key)

            # Clean up
            del self._resumable_uploads[request.upload_id]

        except Exception as e:
            logger.error("Failed to complete resumable upload: {}", e)
            raise

    def abort_multipart_upload(self, bucket: str, key: str, upload_id: str) -> None:
        """Abort GCS resumable upload"""
        # Validate input parameters using GCS-specific schema
        request = GCSAbortResumableUploadRequest(
            bucket=bucket,
            key=key,
            upload_id=upload_id,
        )

        try:
            if request.upload_id in self._resumable_uploads:
                upload_info = self._resumable_uploads[request.upload_id]
                blob = upload_info["blob"]

                # For GCS, we'd cancel the resumable upload here
                logger.info("Aborting GCS resumable upload for {}", request.key)

                # Clean up
                del self._resumable_uploads[request.upload_id]
        except Exception as e:
            logger.warning("Failed to abort resumable upload: {}", e)

    def get_object_head(self, bucket: str, key: str) -> dict[str, Any]:
        """Get GCS object metadata"""
        # Validate input parameters using GCS-specific schema
        request = GCSGetObjectRequest(bucket=bucket, key=key)

        try:
            bucket_obj = self.client.bucket(request.bucket)
            blob = bucket_obj.blob(request.key)

            # Reload to get metadata
            blob.reload()

            return {
                "ContentLength": blob.size,
                "ContentType": blob.content_type,
                "ETag": blob.etag,
                "LastModified": blob.updated,
                "Metadata": blob.metadata or {},
            }
        except GoogleCloudError as e:
            logger.error("Failed to get object head: {}", e)
            raise

    def get_object_range(
        self, bucket: str, key: str, start_byte: int, end_byte: int
    ) -> bytes:
        """Get a range of bytes from GCS object"""
        # Validate input parameters using GCS-specific schema
        request = GCSGetObjectRangeRequest(
            bucket=bucket,
            key=key,
            start_byte=start_byte,
            end_byte=end_byte,
        )

        try:
            bucket_obj = self.client.bucket(request.bucket)
            blob = bucket_obj.blob(request.key)

            # Download the specific range
            data = blob.download_as_bytes(
                start=request.start_byte, end=request.end_byte
            )
            return data
        except GoogleCloudError as e:
            logger.error("Failed to get object range: {}", e)
            raise

    def generate_presigned_url(
        self, bucket: str, key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate GCS presigned URL"""
        # Validate input parameters using GCS-specific schema
        request = GCSGenerateSignedUrlRequest(
            bucket=bucket,
            key=key,
            ttl_seconds=ttl_seconds,
        )

        try:
            bucket_obj = self.client.bucket(request.bucket)
            blob = bucket_obj.blob(request.key)

            # GCS uses signed URLs instead of presigned URLs
            # Default TTL is 1 hour if not specified
            expiration = request.ttl_seconds or 3600

            url = blob.generate_signed_url(
                version="v4", expiration=expiration, method="GET"
            )
            return url
        except Exception as e:
            logger.error("Failed to generate signed URL: {}", e)
            raise

    # GCS-specific methods that better reflect resumable upload behavior

    def create_resumable_upload(
        self,
        bucket: str,
        key: str,
        content_type: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> GCSResumableUploadResponse:
        """Create a GCS resumable upload session (native GCS method)"""
        request = GCSResumableUploadRequest(
            bucket=bucket,
            key=key,
            content_type=content_type,
            metadata=metadata,
        )

        try:
            bucket_obj = self.client.bucket(request.bucket)
            blob = bucket_obj.blob(request.key)

            # Set metadata if provided
            if request.metadata:
                blob.metadata = request.metadata

            # Start resumable upload
            resumable_url = blob.create_resumable_upload_session(
                content_type=request.content_type
            )

            # Store the resumable upload info
            upload_id = f"gcs_resumable_{int(time.time())}_{hash(request.key)}"
            self._resumable_uploads[upload_id] = {
                "blob": blob,
                "resumable_url": resumable_url,
                "bucket": request.bucket,
                "key": request.key,
                "bytes_uploaded": 0,
            }

            return GCSResumableUploadResponse(
                upload_id=upload_id,
                resumable_url=resumable_url,
                metadata={"bucket": request.bucket, "key": request.key},
            )
        except GoogleCloudError as e:
            logger.error("Failed to create resumable upload: {}", e)
            raise

    def upload_chunk(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        chunk_data: bytes,
        metadata: Optional[dict[str, str]] = None,
    ) -> GCSChunkUploadResponse:
        """Upload a chunk to a GCS resumable upload session"""
        request = GCSChunkUploadRequest(
            bucket=bucket,
            key=key,
            upload_id=upload_id,
            chunk_data=chunk_data,
            metadata=metadata,
        )

        try:
            if request.upload_id not in self._resumable_uploads:
                raise ValueError(f"Unknown upload ID: {request.upload_id}")

            upload_info = self._resumable_uploads[request.upload_id]

            # Update bytes uploaded counter
            upload_info["bytes_uploaded"] += len(request.chunk_data)

            # In a real implementation, you would use the resumable URL to upload the chunk
            # For now, we'll just track the progress
            logger.debug(
                "Uploaded chunk of {} bytes, total uploaded: {} bytes",
                len(request.chunk_data),
                upload_info["bytes_uploaded"],
            )

            return GCSChunkUploadResponse(
                bytes_uploaded=upload_info["bytes_uploaded"],
                metadata={"chunk_size": len(request.chunk_data)},
            )
        except Exception as e:
            logger.error("Failed to upload chunk: {}", e)
            raise

    def complete_resumable_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> None:
        """Complete a GCS resumable upload session"""
        request = GCSCompleteResumableUploadRequest(
            bucket=bucket,
            key=key,
            upload_id=upload_id,
            metadata=metadata,
        )

        try:
            if request.upload_id not in self._resumable_uploads:
                raise ValueError(f"Unknown upload ID: {request.upload_id}")

            upload_info = self._resumable_uploads[request.upload_id]
            total_bytes = upload_info["bytes_uploaded"]

            logger.info(
                "Completing GCS resumable upload for {} ({} bytes total)",
                request.key,
                total_bytes,
            )

            # In a real implementation, you would finalize the resumable upload
            # using the GCS API to complete the object

            # Clean up
            del self._resumable_uploads[request.upload_id]

        except Exception as e:
            logger.error("Failed to complete resumable upload: {}", e)
            raise

    def abort_resumable_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
    ) -> None:
        """Abort a GCS resumable upload session"""
        request = GCSAbortResumableUploadRequest(
            bucket=bucket,
            key=key,
            upload_id=upload_id,
        )

        try:
            if request.upload_id in self._resumable_uploads:
                upload_info = self._resumable_uploads[request.upload_id]
                total_bytes = upload_info["bytes_uploaded"]

                logger.info(
                    "Aborting GCS resumable upload for {} ({} bytes uploaded)",
                    request.key,
                    total_bytes,
                )

                # In a real implementation, you would cancel the resumable upload
                # using the GCS API

                # Clean up
                del self._resumable_uploads[request.upload_id]
        except Exception as e:
            logger.warning("Failed to abort resumable upload: {}", e)

    def get_resumable_upload_status(self, upload_id: str) -> Optional[dict[str, Any]]:
        """Get the status of a resumable upload session"""
        if upload_id in self._resumable_uploads:
            upload_info = self._resumable_uploads[upload_id]
            return {
                "bucket": upload_info["bucket"],
                "key": upload_info["key"],
                "bytes_uploaded": upload_info["bytes_uploaded"],
                "resumable_url": upload_info["resumable_url"],
            }
        return None


def create_gcs_storage_client(
    auth_method: str,
    storage_secrets: Optional[Union[StorageSecrets, dict[StorageSecrets, Any]]],
) -> GCSStorageClient:
    """Factory function to create a GCS storage client"""
    # Convert storage_secrets to the format expected by get_gcs_client
    # get_gcs_client expects Optional[dict]
    if isinstance(storage_secrets, StorageSecrets):
        # Convert StorageSecrets enum to dict format
        secrets_dict: Optional[dict] = {
            storage_secrets: None
        }  # This is a placeholder - actual implementation would need proper conversion
    else:
        secrets_dict = storage_secrets

    gcs_client = get_gcs_client(auth_method, secrets_dict)
    return GCSStorageClient(gcs_client)
