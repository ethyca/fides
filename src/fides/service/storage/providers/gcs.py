from typing import Any, Dict, IO, Optional, Union
from io import BytesIO

import smart_open

from google.oauth2 import service_account

from loguru import logger

from fideslang.validation import AnyHttpUrlString
from .base import StorageProvider, StorageResponse, StorageMetadata

from fides.api.schemas.storage.storage import GCSAuthMethod
from fides.api.service.storage.gcs import get_gcs_client


class GCSStorageProvider(StorageProvider):
    """
    Google Cloud Storage provider implementation using smart_open for streaming operations.
    Supports both standard uploads and streaming for large files.
    """

    def __init__(self, configuration: Dict[str, Any]):
        super().__init__(configuration)
        self.bucket_name = configuration["bucket_name"]
        self.auth_method = configuration["auth_method"]
        self.storage_secrets = configuration.get("secrets", {})

        # Initialize GCS client
        self._gcs_client = None

    @property
    def gcs_client(self):
        """Lazy initialize GCS client"""
        if self._gcs_client is None:
            self._gcs_client = get_gcs_client(self.auth_method, self.storage_secrets)
        return self._gcs_client

    def _build_gcs_uri(self, file_key: str) -> str:
        """Build GCS URI for smart_open"""
        return f"gs://{self.bucket_name}/{file_key}"

    def _get_transport_params(self) -> Dict[str, Any]:
        """Get transport parameters for smart_open GCS operations"""
        transport_params = {}

        if (
            self.auth_method == GCSAuthMethod.SERVICE_ACCOUNT_KEYS.value
            and self.storage_secrets
        ):
            # smart_open can use service account credentials from dict
            transport_params["credentials"] = (
                service_account.Credentials.from_service_account_info(
                    dict(self.storage_secrets)
                )
            )

        return transport_params

    def store_file(
        self,
        file_content: Union[IO[bytes], bytes, BytesIO],
        file_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageResponse:
        """Store a file to GCS using smart_open for streaming efficiency"""
        try:
            uri = self._build_gcs_uri(file_key)
            transport_params = self._get_transport_params()

            # Add content type if provided
            if content_type:
                transport_params["content_type"] = content_type

            # Add metadata if provided
            if metadata:
                transport_params["metadata"] = metadata

            with smart_open.open(
                uri, "wb", transport_params=transport_params
            ) as gcs_file:
                if hasattr(file_content, "read"):
                    # File-like object
                    while chunk := file_content.read(8192):  # 8KB chunks
                        gcs_file.write(chunk)
                elif isinstance(file_content, (bytes, bytearray)):
                    gcs_file.write(file_content)
                else:
                    raise ValueError(
                        f"Unsupported file_content type: {type(file_content)}"
                    )

            # Get file size for response
            try:
                file_size = self._get_file_size(file_key)
            except Exception as e:
                logger.warning(f"Could not determine file size for {file_key}: {e}")
                file_size = None

            return StorageResponse(
                success=True,
                file_size=file_size,
                metadata=StorageMetadata(
                    content_type=content_type, custom_metadata=metadata
                ),
            )

        except Exception as e:
            logger.error(f"Failed to upload to GCS: {e}")
            return StorageResponse(success=False, error_message=str(e))

    def retrieve_file(
        self, file_key: str, get_content: bool = False
    ) -> StorageResponse:
        """Retrieve a file from GCS"""
        try:
            if get_content:
                uri = self._build_gcs_uri(file_key)
                transport_params = self._get_transport_params()

                with smart_open.open(
                    uri, "rb", transport_params=transport_params
                ) as gcs_file:
                    content = gcs_file.read()

                return StorageResponse(
                    success=True,
                    file_size=len(content),
                    metadata=StorageMetadata(file_size=len(content)),
                )
            else:
                # Just check if file exists and get metadata
                file_size = self._get_file_size(file_key)
                return StorageResponse(
                    success=True,
                    file_size=file_size,
                    metadata=StorageMetadata(file_size=file_size),
                )

        except Exception as e:
            logger.error(f"Failed to retrieve from GCS: {e}")
            return StorageResponse(success=False, error_message=str(e))

    def delete_file(self, file_key: str) -> StorageResponse:
        """Delete a file from GCS"""
        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(file_key)
            blob.delete()

            return StorageResponse(success=True)

        except Exception as e:
            logger.error(f"Failed to delete from GCS: {e}")
            return StorageResponse(success=False, error_message=str(e))

    def generate_presigned_url(
        self, file_key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate a signed URL for the GCS object"""
        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(file_key)

            # Default TTL if not provided
            from datetime import timedelta

            ttl = timedelta(seconds=ttl_seconds or 3600)  # 1 hour default

            return blob.generate_signed_url(version="v4", expiration=ttl, method="GET")
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for GCS: {e}")
            raise

    def stream_upload(self, file_key: str) -> IO[bytes]:
        """Get a writable stream for uploading to GCS"""
        uri = self._build_gcs_uri(file_key)
        transport_params = self._get_transport_params()

        return smart_open.open(uri, "wb", transport_params=transport_params)

    def stream_download(self, file_key: str) -> IO[bytes]:
        """Get a readable stream for downloading from GCS"""
        uri = self._build_gcs_uri(file_key)
        transport_params = self._get_transport_params()

        return smart_open.open(uri, "rb", transport_params=transport_params)

    def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in GCS"""
        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(file_key)
            return blob.exists()
        except Exception:
            return False

    def validate_configuration(self) -> bool:
        """Validate the GCS configuration and credentials"""
        try:
            # Test connection by checking if bucket exists
            bucket = self.gcs_client.bucket(self.bucket_name)
            bucket.reload()  # This will fail if credentials are invalid
            return True
        except Exception as e:
            logger.error(f"GCS configuration validation failed: {e}")
            return False

    def _get_file_size(self, file_key: str) -> Optional[int]:
        """Get the size of a file in GCS"""
        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(file_key)
            blob.reload()
            return blob.size
        except Exception:
            return None
