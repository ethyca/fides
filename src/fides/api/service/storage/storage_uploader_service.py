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
from fides.api.service.storage.streaming.s3.streaming_s3 import upload_to_s3_streaming
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
    Retrieves storage configs and calls appropriate upload method
    :param db: SQLAlchemy Session
    :param request_id: Request id
    :param data: Dict of data to upload
    :param storage_key: Key representing where to upload data
    :return str representing location of upload (url or simply a description of where to find the data)
    """
    logger.debug("upload called with storage_key: {}", storage_key)

    config: Optional[StorageConfig] = StorageConfig.get_by(
        db=db, field="key", value=storage_key
    )

    if config is None:
        logger.warning("Storage type not found: {}", storage_key)
        raise StorageUploadError(f"Storage type not found: {storage_key}")

    logger.debug(
        "Retrieved storage config: key={}, type={}, has_secrets={}",
        config.key,
        config.type,
        config.secrets is not None,
    )

    if config.secrets:
        logger.debug("Storage config secrets type: {}", type(config.secrets))
        if isinstance(config.secrets, dict):
            logger.debug("Storage config secrets keys: {}", list(config.secrets.keys()))
        else:
            logger.debug("Storage config secrets is not a dict: {}", config.secrets)
    else:
        logger.warning("Storage config has no secrets!")

    uploader: Any = _get_uploader_from_config_type(config.type)  # type: ignore
    logger.debug(
        "Using uploader: {}",
        uploader.__name__ if hasattr(uploader, "__name__") else type(uploader),
    )

    return uploader(db, config, data, privacy_request)


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
    _: Session,
    config: StorageConfig,
    data: Dict,
    privacy_request: PrivacyRequest,
) -> str:
    """
    Constructs necessary info needed for s3 before calling upload.
    If `enable_streaming` is configured in the storage config, we use a streaming approach for better memory efficiency.
    Otherwise we fall back to the traditional upload method.
    """
    logger.debug(
        "_s3_uploader called with config: key={}, type={}, has_secrets={}",
        config.key,
        config.type,
        config.secrets is not None,
    )

    if config.secrets:
        logger.debug(
            "Config secrets keys: {}",
            (
                list(config.secrets.keys())
                if isinstance(config.secrets, dict)
                else "Not a dict"
            ),
        )
        logger.debug("Config secrets type: {}", type(config.secrets))
    else:
        logger.warning("Config secrets is None or empty!")

    enable_streaming = config.details.get(StorageDetails.ENABLE_STREAMING.value, False)
    file_key: str = _construct_file_key(privacy_request.id, config, enable_streaming)

    bucket_name = config.details[StorageDetails.BUCKET.value]
    auth_method = config.details[StorageDetails.AUTH_METHOD.value]
    document = None

    if enable_streaming:
        file_key = f"{privacy_request.id}.zip"
        # Use streaming upload for better memory efficiency
        logger.debug("Using streaming S3 upload for {}", file_key)
        logger.debug("Calling upload_to_s3_streaming with secrets: {}", config.secrets)
        return upload_to_s3_streaming(
            config.secrets,  # type: ignore
            data,
            bucket_name,
            file_key,
            config.format.value,  # type: ignore
            privacy_request,
            document,
            auth_method,
        )

    file_key = _construct_file_key(privacy_request.id, config)

    # Fall back to traditional upload method
    logger.debug("Using traditional S3 upload for {}", file_key)
    return upload_to_s3(
        config.secrets,  # type: ignore
        data,
        bucket_name,
        file_key,
        config.format.value,  # type: ignore
        privacy_request,
        document,
        auth_method,
    )


def _gcs_uploader(
    _: Session,
    config: StorageConfig,
    data: Dict,
    privacy_request: PrivacyRequest,
) -> str:
    """Constructs necessary info needed for Google Cloud Storage before calling upload"""
    file_key: str = _construct_file_key(privacy_request.id, config)

    bucket_name = config.details[StorageDetails.BUCKET.value]
    auth_method = config.details[StorageDetails.AUTH_METHOD.value]

    return upload_to_gcs(
        config.secrets,
        data,
        bucket_name,
        file_key,
        config.format.value,  # type: ignore
        privacy_request,
        auth_method,
    )


def _local_uploader(
    _: Session,
    config: StorageConfig,
    data: Dict,
    privacy_request: PrivacyRequest,
) -> str:
    """Uploads data to local storage, used for quick-start/demo purposes"""
    file_key: str = _construct_file_key(privacy_request.id, config)
    return upload_to_local(data, file_key, privacy_request, config.format.value)  # type: ignore
