import os
from io import BytesIO
from typing import IO, Any, Dict, Optional, Union

import smart_open
from botocore.exceptions import ClientError, NoCredentialsError
from fideslang.validation import AnyHttpUrlString
from loguru import logger

from fides.api.common_exceptions import StorageUploadError
from fides.api.schemas.storage.storage import AWSAuthMethod, StorageSecrets
from fides.api.service.storage.s3 import create_presigned_url_for_s3, get_s3_client
from fides.api.util.aws_util import get_aws_session

from .base import StorageMetadata, StorageProvider, StorageResponse


class S3StorageProvider(StorageProvider):
    """
    S3 storage provider implementation using smart_open for streaming operations.
    Supports both standard uploads and streaming for large files.
    """

    def __init__(self, configuration: Dict[str, Any]):
        super().__init__(configuration)
        self.bucket_name = configuration["bucket_name"]
        self.auth_method = configuration["auth_method"]
        self.storage_secrets = configuration.get("secrets", {})
        self.region_name = configuration.get("region_name", "us-east-1")

        # Initialize S3 client for presigned URLs
        self._s3_client = None

    @property
    def s3_client(self):
        """Lazy initialize S3 client"""
        if self._s3_client is None:
            self._s3_client = get_s3_client(self.auth_method, self.storage_secrets)
        return self._s3_client

    def _build_s3_uri(self, file_key: str) -> str:
        """Build S3 URI for smart_open"""
        return f"s3://{self.bucket_name}/{file_key}"

    def _get_transport_params(self) -> Dict[str, Any]:
        """Get transport parameters for smart_open S3 operations"""
        transport_params = {}

        if self.auth_method == AWSAuthMethod.SECRET_KEYS.value:
            transport_params.update(
                {
                    "aws_access_key_id": self.storage_secrets.get(
                        StorageSecrets.AWS_ACCESS_KEY_ID.value
                    ),
                    "aws_secret_access_key": self.storage_secrets.get(
                        StorageSecrets.AWS_SECRET_ACCESS_KEY.value
                    ),
                }
            )

        if self.region_name:
            transport_params["region_name"] = self.region_name

        return transport_params

    def store_file(
        self,
        file_content: Union[IO[bytes], bytes, BytesIO],
        file_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageResponse:
        """Store a file to S3 using smart_open for streaming efficiency"""
        try:
            uri = self._build_s3_uri(file_key)
            transport_params = self._get_transport_params()

            # Add content type if provided
            if content_type:
                transport_params["content_type"] = content_type

            # Add metadata if provided
            if metadata:
                transport_params["resource_kwargs"] = {"Metadata": metadata}

            with smart_open.open(
                uri, "wb", transport_params=transport_params
            ) as s3_file:
                if hasattr(file_content, "read"):
                    # File-like object
                    while chunk := file_content.read(8192):  # 8KB chunks
                        s3_file.write(chunk)
                elif isinstance(file_content, (bytes, bytearray)):
                    s3_file.write(file_content)
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
            logger.error(f"Failed to upload to S3: {e}")
            return StorageResponse(success=False, error_message=str(e))

    def retrieve_file(
        self, file_key: str, get_content: bool = False
    ) -> StorageResponse:
        """Retrieve a file from S3"""
        try:
            if get_content:
                uri = self._build_s3_uri(file_key)
                transport_params = self._get_transport_params()

                with smart_open.open(
                    uri, "rb", transport_params=transport_params
                ) as s3_file:
                    content = s3_file.read()

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
            logger.error(f"Failed to retrieve from S3: {e}")
            return StorageResponse(success=False, error_message=str(e))

    def delete_file(self, file_key: str) -> StorageResponse:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)

            return StorageResponse(success=True)

        except Exception as e:
            logger.error(f"Failed to delete from S3: {e}")
            return StorageResponse(success=False, error_message=str(e))

    def generate_presigned_url(
        self, file_key: str, ttl_seconds: Optional[int] = None
    ) -> AnyHttpUrlString:
        """Generate a presigned URL for the S3 object"""
        return create_presigned_url_for_s3(
            self.s3_client, self.bucket_name, file_key, ttl_seconds
        )

    def stream_upload(self, file_key: str) -> IO[bytes]:
        """Get a writable stream for uploading to S3"""
        uri = self._build_s3_uri(file_key)
        transport_params = self._get_transport_params()

        return smart_open.open(uri, "wb", transport_params=transport_params)

    def stream_download(self, file_key: str) -> IO[bytes]:
        """Get a readable stream for downloading from S3"""
        uri = self._build_s3_uri(file_key)
        transport_params = self._get_transport_params()

        return smart_open.open(uri, "rb", transport_params=transport_params)

    def file_exists(self, file_key: str) -> bool:
        """Check if a file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def validate_configuration(self) -> bool:
        """Validate the S3 configuration and credentials"""
        try:
            # Test connection by listing bucket (this will fail if credentials are invalid)
            self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            return True
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"S3 configuration validation failed: {e}")
            return False

    def _get_file_size(self, file_key: str) -> Optional[int]:
        """Get the size of a file in S3"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return response.get("ContentLength")
        except Exception:
            return None
