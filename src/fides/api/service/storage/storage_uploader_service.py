from typing import Any, Dict, Optional, Set

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

# REMOVED: from fides.api.common_exceptions import StorageUploadError
# Now handled by PrivacyRequestStorageService
from fides.api.graph.graph import DataCategoryFieldMapping
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import (
    FileNaming,
    ResponseFormat,
    StorageDetails,
    StorageType,
)
from fides.api.service.storage.streaming.s3.streaming_s3 import upload_to_s3_streaming

# Import functions for testing interface compatibility - they now delegate to unified services
from fides.api.tasks.storage import upload_to_gcs, upload_to_local, upload_to_s3


def upload(
    db: Session,
    privacy_request: PrivacyRequest,
    data: Dict,
    storage_key: FidesKey,
    data_category_field_mapping: Optional[DataCategoryFieldMapping] = None,
    data_use_map: Optional[Dict[str, Set[str]]] = None,
) -> str:
    """
    DEPRECATED: Use PrivacyRequestStorageService instead.

    This function is deprecated and will be removed in a future version.
    Use PrivacyRequestStorageService.upload_privacy_request_data() which provides
    the same functionality through the unified StorageService interface.

    Retrieves storage configs and calls appropriate upload method
    :param db: SQLAlchemy Session
    :param request_id: Request id
    :param data: Dict of data to upload
    :param storage_key: Key representing where to upload data
    :return str representing location of upload (url or simply a description of where to find the data)
    """
    from fides.service.storage import PrivacyRequestStorageService

    logger.warning(
        "storage_uploader_service.upload is deprecated. Use PrivacyRequestStorageService instead."
    )

    # Delegate to new unified service
    storage_service = PrivacyRequestStorageService(db)
    return storage_service.upload_privacy_request_data(
        privacy_request=privacy_request,
        data=data,
        storage_key=storage_key,
        data_category_field_mapping=data_category_field_mapping,
        data_use_map=data_use_map,
    )


def get_extension(resp_format: ResponseFormat, enable_streaming: bool = False) -> str:
    """
    Determine file extension for various response formats.

    CSV's and HTML reports are zipped together before uploading to s3.
    """
    if enable_streaming:
        return "zip"

    if resp_format == ResponseFormat.csv:
        return "zip"

    if resp_format == ResponseFormat.json:
        return "json"

    if resp_format == ResponseFormat.html:
        return "zip"

    raise NotImplementedError(f"No extension defined for {resp_format}")


def _construct_file_key(
    request_id: str, config: StorageConfig, enable_streaming: bool = False
) -> str:
    """Constructs file key based on desired naming convention and request id, e.g. 23847234.json"""
    naming = config.details.get(
        StorageDetails.NAMING.value, FileNaming.request_id.value
    )
    if naming != FileNaming.request_id.value:
        raise ValueError(f"File naming of {naming} not supported")

    return f"{request_id}.{get_extension(config.format, enable_streaming)}"  # type: ignore


def _get_uploader_from_config_type(storage_type: StorageType) -> Any:
    """Determines which uploader method to use based on storage type"""
    return {
        StorageType.s3.value: _s3_uploader,
        StorageType.local.value: _local_uploader,
        StorageType.gcs.value: _gcs_uploader,
    }[storage_type.value]


def _s3_uploader(
    db: Session,
    config: StorageConfig,
    data: Dict,
    privacy_request: PrivacyRequest,
) -> str:
    """
    DEPRECATED: Use PrivacyRequestStorageService instead.

    Constructs necessary info needed for s3 before calling upload.
    If `enable_streaming` is configured in the storage config, we use a streaming approach for better memory efficiency.
    Otherwise we fall back to the traditional upload method.
    """
    logger.warning(
        "_s3_uploader is deprecated. Use PrivacyRequestStorageService instead."
    )

    # Create service and delegate to unified interface
    from fides.service.storage import PrivacyRequestStorageService

    storage_service = PrivacyRequestStorageService(db)
    return storage_service.upload_privacy_request_data(
        privacy_request=privacy_request,
        data=data,
        storage_key=config.key,
    )


def _gcs_uploader(
    db: Session,
    config: StorageConfig,
    data: Dict,
    privacy_request: PrivacyRequest,
) -> str:
    """DEPRECATED: Use PrivacyRequestStorageService instead."""
    from fides.service.storage import PrivacyRequestStorageService

    logger.warning(
        "_gcs_uploader is deprecated. Use PrivacyRequestStorageService instead."
    )

    # Create service and delegate to unified interface
    storage_service = PrivacyRequestStorageService(db)
    return storage_service.upload_privacy_request_data(
        privacy_request=privacy_request,
        data=data,
        storage_key=config.key,
    )


def _local_uploader(
    db: Session,
    config: StorageConfig,
    data: Dict,
    privacy_request: PrivacyRequest,
) -> str:
    """DEPRECATED: Use PrivacyRequestStorageService instead."""
    from fides.service.storage import PrivacyRequestStorageService

    logger.warning(
        "_local_uploader is deprecated. Use PrivacyRequestStorageService instead."
    )

    # Create service and delegate to unified interface
    storage_service = PrivacyRequestStorageService(db)
    return storage_service.upload_privacy_request_data(
        privacy_request=privacy_request,
        data=data,
        storage_key=config.key,
    )


# Export functions for testing interface compatibility
# These maintain the same signatures as the original functions for tests
__all__ = [
    "upload",
    "get_extension",
    "upload_to_s3",
    "upload_to_gcs",
    "upload_to_local",
    "upload_to_s3_streaming",
]
