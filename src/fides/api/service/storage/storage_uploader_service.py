from typing import Any, Dict, Optional, Set

from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import StorageUploadError
from fides.api.graph.graph import DataCategoryFieldMapping
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import (
    FileNaming,
    ResponseFormat,
    StorageDetails,
    StorageType,
)
from fides.api.tasks.storage import upload_to_local, upload_to_s3


def upload(
    db: Session,
    privacy_request: PrivacyRequest,
    data: Dict,
    storage_key: FidesKey,
    data_category_field_mapping: Optional[DataCategoryFieldMapping] = None,
    data_use_map: Optional[Dict[str, Set[str]]] = None,
) -> str:
    """
    Retrieves storage configs and calls appropriate upload method
    :param db: SQLAlchemy Session
    :param request_id: Request id
    :param data: Dict of data to upload
    :param storage_key: Key representing where to upload data
    :return str representing location of upload (url or simply a description of where to find the data)
    """
    config: Optional[StorageConfig] = StorageConfig.get_by(
        db=db, field="key", value=storage_key
    )

    if config is None:
        logger.warning("Storage type not found: {}", storage_key)
        raise StorageUploadError(f"Storage type not found: {storage_key}")
    uploader: Any = _get_uploader_from_config_type(config.type)  # type: ignore
    return uploader(
        db, config, data, privacy_request, data_category_field_mapping, data_use_map
    )


def get_extension(resp_format: ResponseFormat) -> str:
    """
    Determine file extension for various response formats.

    CSV's and HTML reports are zipped together before uploading to s3.
    """
    if resp_format == ResponseFormat.csv:
        return "zip"

    if resp_format == ResponseFormat.json:
        return "json"

    if resp_format == ResponseFormat.html:
        return "zip"

    raise NotImplementedError(f"No extension defined for {resp_format}")


def _construct_file_key(request_id: str, config: StorageConfig) -> str:
    """Constructs file key based on desired naming convention and request id, e.g. 23847234.json"""
    naming = config.details.get(
        StorageDetails.NAMING.value, FileNaming.request_id.value
    )
    if naming != FileNaming.request_id.value:
        raise ValueError(f"File naming of {naming} not supported")

    return f"{request_id}.{get_extension(config.format)}"  # type: ignore


def _get_uploader_from_config_type(storage_type: StorageType) -> Any:
    """Determines which uploader method to use based on storage type"""
    return {
        StorageType.s3.value: _s3_uploader,
        StorageType.local.value: _local_uploader,
    }[storage_type.value]


def _s3_uploader(
    _: Session,
    config: StorageConfig,
    data: Dict,
    privacy_request: PrivacyRequest,
    data_category_field_mapping: Optional[DataCategoryFieldMapping] = None,
    data_use_map: Optional[Dict[str, Set[str]]] = None,
) -> str:
    """Constructs necessary info needed for s3 before calling upload"""
    file_key: str = _construct_file_key(privacy_request.id, config)

    bucket_name = config.details[StorageDetails.BUCKET.value]
    auth_method = config.details[StorageDetails.AUTH_METHOD.value]

    return upload_to_s3(
        config.secrets,  # type: ignore
        data,
        bucket_name,
        file_key,
        config.format.value,  # type: ignore
        privacy_request,
        auth_method,
        data_category_field_mapping,
        data_use_map,
    )


def _local_uploader(
    _: Session,
    config: StorageConfig,
    data: Dict,
    privacy_request: PrivacyRequest,
    data_category_field_mapping: Optional[DataCategoryFieldMapping] = None,
    data_use_map: Optional[Dict[str, Set[str]]] = None,
) -> str:
    """Uploads data to local storage, used for quick-start/demo purposes"""
    file_key: str = _construct_file_key(privacy_request.id, config)
    return upload_to_local(data, file_key, privacy_request, config.format.value, data_category_field_mapping, data_use_map)  # type: ignore
