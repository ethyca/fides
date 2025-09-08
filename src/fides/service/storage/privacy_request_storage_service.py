"""
PrivacyRequestStorageService handles storage operations for privacy request data exports.
Clean separation of concerns using the unified StorageService.
"""

from typing import Dict, Optional, Set, Any, TYPE_CHECKING
from sqlalchemy.orm import Session
from loguru import logger

from fideslang.validation import FidesKey, AnyHttpUrlString
from fides.api.common_exceptions import StorageUploadError
from fides.api.graph.graph import DataCategoryFieldMapping
from fides.api.models.storage import StorageConfig

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.storage.storage import (
    FileNaming,
    ResponseFormat,
    StorageDetails,
)
from fides.api.tasks.storage import write_to_in_memory_buffer
from fides.service.storage import StorageService


class PrivacyRequestStorageService:
    """
    Service for handling privacy request data export storage operations.

    Provides a clean interface for uploading privacy request data to various storage backends
    using the unified StorageService.
    """

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db

    def upload_privacy_request_data(
        self,
        privacy_request,  # PrivacyRequest - using TYPE_CHECKING to avoid circular import
        data: Dict[str, Any],
        storage_key: FidesKey,
        data_category_field_mapping: Optional[DataCategoryFieldMapping] = None,
        data_use_map: Optional[Dict[str, Set[str]]] = None,
    ) -> AnyHttpUrlString:
        """
        Upload privacy request data to storage and return download URL.

        Args:
            privacy_request: The privacy request instance
            data: Dictionary of data to upload
            storage_key: Key representing where to upload data
            data_category_field_mapping: Optional field mapping for data categories
            data_use_map: Optional data use mapping

        Returns:
            Download URL for the uploaded data

        Raises:
            StorageUploadError: If upload fails
        """
        logger.debug(
            "Starting privacy request data upload with storage_key: {}", storage_key
        )

        # Get storage configuration
        storage_config: StorageConfig = StorageConfig.get_by(
            db=self.db, field="key", value=storage_key
        )
        if not storage_config:
            raise StorageUploadError(f"Storage configuration not found: {storage_key}")

        logger.debug(
            "Retrieved storage config: key={}, type={}, format={}, has_secrets={}",
            storage_config.key,
            storage_config.type,
            storage_config.format,
            storage_config.secrets is not None,
        )

        if not storage_config.secrets:
            logger.warning("Storage config has no secrets!")

        try:
            # Create unified storage service
            storage_service = StorageService.from_config(storage_config)

            # Check if streaming is enabled
            enable_streaming = storage_config.details.get(
                StorageDetails.ENABLE_STREAMING.value, False
            )

            if enable_streaming:
                # Use streaming approach for large data
                return self._upload_streaming(
                    storage_service, privacy_request, data, storage_config
                )

            # Use standard upload
            return self._upload_standard(
                storage_service, privacy_request, data, storage_config
            )

        except Exception as e:
            logger.error(f"Failed to upload privacy request data: {e}")
            raise StorageUploadError(f"Upload failed: {e}")

    def _upload_standard(
        self,
        storage_service: StorageService,
        privacy_request,  # PrivacyRequest
        data: Dict[str, Any],
        storage_config: StorageConfig,
    ) -> AnyHttpUrlString:
        """Standard upload for privacy request data."""

        # Construct file key
        file_key = self._construct_file_key(privacy_request.id, storage_config)

        # Use existing formatting logic to prepare file content
        file_content = write_to_in_memory_buffer(
            storage_config.format.value, data, privacy_request
        )

        # Determine content type based on format
        content_type = self._get_content_type_for_format(storage_config.format)

        # Upload file
        response = storage_service.store_file(
            file_content=file_content,
            file_key=file_key,
            content_type=content_type,
            metadata={
                "privacy_request_id": privacy_request.id,
                "format": storage_config.format.value,
                "upload_type": "standard",
                "created_by": "PrivacyRequestStorageService",
            },
        )

        if not response.success:
            raise StorageUploadError(f"Storage upload failed: {response.error_message}")

        # Generate download URL
        download_url = storage_service.generate_presigned_url(file_key)

        logger.info(
            f"Successfully uploaded privacy request {privacy_request.id} data "
            f"(format: {storage_config.format.value}, size: {response.file_size} bytes)"
        )

        return download_url

    def _upload_streaming(
        self,
        storage_service: StorageService,
        privacy_request,  # PrivacyRequest
        data: Dict[str, Any],
        storage_config: StorageConfig,
    ) -> AnyHttpUrlString:
        """Streaming upload for large privacy request data."""

        # For streaming, use ZIP format
        file_key = f"{privacy_request.id}.zip"

        # Use unified StorageService for streaming upload
        try:
            logger.debug(
                f"Starting unified streaming upload for privacy request {privacy_request.id}"
            )

            # Create streaming ZIP content and upload directly using StorageService
            with storage_service.stream_upload(file_key) as upload_stream:
                # Generate ZIP content for streaming (reuses existing DSR logic)
                zip_content = write_to_in_memory_buffer(
                    storage_config.format.value, data, privacy_request
                )

                # Stream the ZIP content directly to storage
                upload_stream.write(zip_content.getvalue())

            # Generate download URL using unified service
            download_url = storage_service.generate_presigned_url(file_key)

            logger.info(
                f"Successfully uploaded privacy request {privacy_request.id} data using unified streaming "
                f"(format: ZIP, provider: {storage_service.provider_type})"
            )

            return download_url

        except Exception as e:
            # Fallback to standard upload if streaming fails
            logger.warning(
                f"Unified streaming upload failed, falling back to standard: {e}"
            )
            return self._upload_standard(
                storage_service, privacy_request, data, storage_config
            )

    def _construct_file_key(
        self,
        request_id: str,
        storage_config: StorageConfig,
        enable_streaming: bool = False,
    ) -> str:
        """Construct file key based on naming convention and request ID."""
        naming = storage_config.details.get(
            StorageDetails.NAMING.value, FileNaming.request_id.value
        )

        if naming != FileNaming.request_id.value:
            raise ValueError(f"File naming of {naming} not supported")

        extension = self._get_extension(storage_config.format, enable_streaming)
        return f"{request_id}.{extension}"

    def _get_extension(
        self, response_format: ResponseFormat, enable_streaming: bool = False
    ) -> str:
        """Determine file extension for various response formats."""
        if enable_streaming:
            return "zip"

        if response_format == ResponseFormat.csv:
            return "zip"
        if response_format == ResponseFormat.json:
            return "json"
        if response_format == ResponseFormat.html:
            return "zip"

    def _get_content_type_for_format(self, response_format: ResponseFormat) -> str:
        """Get content type based on response format."""
        if response_format == ResponseFormat.json:
            return "application/json"
        if response_format == ResponseFormat.csv:
            return "application/zip"
        if response_format == ResponseFormat.html:
            return "application/zip"


# Convenience function to maintain existing API for tests and legacy code
def upload_privacy_request_data(
    db: Session,
    privacy_request,  # PrivacyRequest
    data: Dict[str, Any],
    storage_key: FidesKey,
    data_category_field_mapping: Optional[DataCategoryFieldMapping] = None,
    data_use_map: Optional[Dict[str, Set[str]]] = None,
) -> str:
    """
    Convenience function that maintains the same API as the old upload() function.

    Args:
        db: Database session
        privacy_request: The privacy request instance
        data: Dictionary of data to upload
        storage_key: Key representing where to upload data
        data_category_field_mapping: Optional field mapping for data categories
        data_use_map: Optional data use mapping

    Returns:
        Download URL for the uploaded data
    """
    service = PrivacyRequestStorageService(db)
    return service.upload_privacy_request_data(
        privacy_request=privacy_request,
        data=data,
        storage_key=storage_key,
        data_category_field_mapping=data_category_field_mapping,
        data_use_map=data_use_map,
    )


# Export utility functions for backward compatibility
def get_extension(
    response_format: ResponseFormat, enable_streaming: bool = False
) -> str:
    """Get file extension for response format (for tests and legacy compatibility)."""
    # Direct implementation to avoid creating service instance
    if enable_streaming:
        return "zip"

    if response_format == ResponseFormat.csv:
        return "zip"
    if response_format == ResponseFormat.json:
        return "json"
    if response_format == ResponseFormat.html:
        return "zip"
