import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from fidesops.ops.common_exceptions import StorageUploadError
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.models.storage import StorageConfig
from fidesops.ops.schemas.shared_schemas import FidesOpsKey
from fidesops.ops.schemas.storage.storage import (
    FileNaming,
    ResponseFormat,
    StorageDetails,
    StorageType,
)
from fidesops.ops.tasks.storage import upload_to_local, upload_to_onetrust, upload_to_s3

logger = logging.getLogger(__name__)


def upload(
    db: Session, *, request_id: str, data: Dict, storage_key: FidesOpsKey
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
        logger.warning("Storage type not found: %s", storage_key)
        raise StorageUploadError(f"Storage type not found: {storage_key}")

    uploader: Any = _get_uploader_from_config_type(config.type)  # type: ignore
    return uploader(db, config, data, request_id)


def get_extension(resp_format: ResponseFormat) -> str:
    """
    Determine file extension for various response formats.

    CSV's are zipped together before uploading to s3.
    """
    if resp_format == ResponseFormat.csv:
        return "zip"

    if resp_format == ResponseFormat.json:
        return "json"

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
        StorageType.onetrust.value: _onetrust_uploader,
        StorageType.local.value: _local_uploader,
    }[storage_type.value]


def _s3_uploader(_: Session, config: StorageConfig, data: Dict, request_id: str) -> str:
    """Constructs necessary info needed for s3 before calling upload"""
    file_key: str = _construct_file_key(request_id, config)

    bucket_name = config.details[StorageDetails.BUCKET.value]
    auth_method = config.details[StorageDetails.AUTH_METHOD.value]

    return upload_to_s3(
        config.secrets, data, bucket_name, file_key, config.format.value, request_id, auth_method  # type: ignore
    )


def _onetrust_uploader(
    db: Session, config: StorageConfig, data: Dict, request_id: str
) -> str:

    """Constructs necessary info needed for onetrust before calling upload"""
    request_details: Optional[PrivacyRequest] = PrivacyRequest.get(
        db, object_id=request_id
    )
    if request_details is None:
        raise StorageUploadError(
            f"Request could not be found for request_id: {request_id}"
        )

    payload_data = {
        "language": "en-us",
        "system": config.details[StorageDetails.SERVICE_NAME.value],
        "results": data,
    }
    return upload_to_onetrust(
        payload_data,
        config.secrets,  # type: ignore
        request_details.external_id,  # type: ignore
    )


def _local_uploader(
    _: Session, config: StorageConfig, data: Dict, request_id: str
) -> str:
    """Uploads data to local storage, used for quick-start/demo purposes"""
    file_key: str = _construct_file_key(request_id, config)
    return upload_to_local(data, file_key, request_id)
