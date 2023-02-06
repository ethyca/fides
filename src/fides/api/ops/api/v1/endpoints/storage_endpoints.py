from typing import Dict, List, Optional

from fastapi import Body, Depends, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import conlist
from requests import RequestException
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fides.api.ops.api import deps
from fides.api.ops.api.v1.scope_registry import (
    STORAGE_CREATE_OR_UPDATE,
    STORAGE_DELETE,
    STORAGE_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    STORAGE_ACTIVE_DEFAULT,
    STORAGE_BY_KEY,
    STORAGE_CONFIG,
    STORAGE_DEFAULT,
    STORAGE_DEFAULT_BY_TYPE,
    STORAGE_DEFAULT_SECRETS,
    STORAGE_SECRETS,
    STORAGE_UPLOAD,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import StorageUploadError
from fides.api.ops.models.connectionconfig import ConnectionTestStatus
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.models.storage import (
    StorageConfig,
    default_storage_config_name,
    get_active_default_storage_config,
    get_default_storage_config_by_type,
)
from fides.api.ops.schemas.api import BulkUpdateFailed
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    TestStatusMessage,
)
from fides.api.ops.schemas.storage.data_upload_location_response import DataUpload
from fides.api.ops.schemas.storage.storage import (
    BulkPutStorageConfigResponse,
    StorageDestination,
    StorageDestinationBase,
    StorageDestinationResponse,
    StorageType,
)
from fides.api.ops.schemas.storage.storage_secrets_docs_only import (
    possible_storage_secrets,
)
from fides.api.ops.service.storage.storage_authenticator_service import (
    secrets_are_valid,
)
from fides.api.ops.service.storage.storage_uploader_service import upload
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.logger import Pii
from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.api.ops.util.storage_util import get_schema_for_secrets
from fides.lib.exceptions import KeyOrNameAlreadyExists

router = APIRouter(tags=["Storage"], prefix=V1_URL_PREFIX)


@router.post(
    STORAGE_UPLOAD,
    status_code=HTTP_201_CREATED,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_CREATE_OR_UPDATE])],
    response_model=DataUpload,
)
def upload_data(
    request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    data: Dict = Body(...),
    storage_key: FidesKey = Body(...),
) -> DataUpload:
    """
    Uploads data from an access request to specified storage destination.
    Returns location of data.
    """
    logger.info("Finding privacy request with id '{}'", request_id)

    privacy_request = PrivacyRequest.get(db, object_id=request_id)
    if not privacy_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No privacy with id {request_id}.",
        )

    logger.info("Starting storage upload for request id: {}", request_id)
    try:
        data_location: str = upload(
            db, request_id=request_id, data=data, storage_key=storage_key
        )
    except StorageUploadError as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    except RequestException as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
    return DataUpload(location=data_location)


@router.patch(
    STORAGE_CONFIG,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_CREATE_OR_UPDATE])],
    response_model=BulkPutStorageConfigResponse,
)
def patch_config(
    *,
    db: Session = Depends(deps.get_db),
    storage_configs: conlist(StorageDestination, max_items=50),  # type: ignore
) -> BulkPutStorageConfigResponse:
    """
    Given a list of storage destination elements, create or update corresponding StorageConfig objects
    or report failure.
    """
    created_or_updated: List[StorageConfig] = []
    failed: List[BulkUpdateFailed] = []

    logger.info("Starting bulk upsert for {} storage configs", len(storage_configs))
    for destination in storage_configs:
        try:
            storage_config = StorageConfig.create_or_update(
                db=db, data=destination.dict()
            )
        except KeyOrNameAlreadyExists as exc:
            logger.warning(
                "Create/update failed for storage config {}: {}",
                destination.key,
                exc,
            )
            failure = {
                "message": exc.args[0],
                "data": destination.dict(),
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        except Exception as exc:
            logger.warning(
                "Create/update failed for storage config {}: {}",
                destination.key,
                Pii(str(exc)),
            )
            failed.append(
                BulkUpdateFailed(
                    **{
                        "message": "Error creating or updating storage config.",
                        "data": destination.dict(),
                    }
                )
            )
        else:
            created_or_updated.append(storage_config)

    return BulkPutStorageConfigResponse(succeeded=created_or_updated, failed=failed)


@router.put(
    STORAGE_SECRETS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_CREATE_OR_UPDATE])],
    response_model=TestStatusMessage,
)
def put_config_secrets(
    config_key: FidesKey,
    *,
    db: Session = Depends(deps.get_db),
    unvalidated_storage_secrets: possible_storage_secrets,
    verify: Optional[bool] = True,
) -> TestStatusMessage:
    """
    Add or update secrets for storage config.
    """
    logger.info("Finding storage config with key '{}'", config_key)
    storage_config = StorageConfig.get_by(db=db, field="key", value=config_key)
    if not storage_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No storage configuration with key {config_key}.",
        )
    try:
        secrets_schema = get_schema_for_secrets(
            storage_type=storage_config.type,
            secrets=unvalidated_storage_secrets,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.args[0],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.args[0],
        )

    logger.info("Updating storage config secrets for config with key '{}'", config_key)
    try:
        storage_config.set_secrets(db=db, storage_secrets=secrets_schema.dict())  # type: ignore
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.args[0],
        )

    msg = f"Secrets updated for StorageConfig with key: {config_key}."
    if verify:
        status = secrets_are_valid(secrets_schema, storage_config.type)
        if status:
            logger.info(
                "Storage secrets are valid for config with key '{}'", config_key
            )
        else:
            logger.warning(
                "Storage secrets are invalid for config with key '{}'", config_key
            )

        return TestStatusMessage(
            msg=msg,
            test_status=ConnectionTestStatus.succeeded
            if status
            else ConnectionTestStatus.failed,
        )

    return TestStatusMessage(msg=msg, test_status=None)


@router.get(
    STORAGE_CONFIG,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_READ])],
    response_model=Page[StorageDestinationResponse],
)
def get_configs(
    *, db: Session = Depends(deps.get_db), params: Params = Depends()
) -> AbstractPage[StorageConfig]:
    """
    Retrieves configs for storage.
    """
    logger.info("Finding all storage configurations with pagination params {}", params)
    return paginate(
        StorageConfig.query(db).order_by(StorageConfig.created_at.desc()), params=params
    )


@router.get(
    STORAGE_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_READ])],
    response_model=StorageDestinationResponse,
)
def get_config_by_key(
    config_key: FidesKey, *, db: Session = Depends(deps.get_db)
) -> Optional[StorageConfig]:
    """
    Retrieves configs for storage by key.
    """
    logger.info("Finding storage config with key '{}'", config_key)

    storage_config = StorageConfig.get_by(db, field="key", value=config_key)
    if not storage_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No configuration with key {config_key}.",
        )
    return storage_config


@router.delete(
    STORAGE_BY_KEY,
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_DELETE])],
)
def delete_config_by_key(
    config_key: FidesKey, *, db: Session = Depends(deps.get_db)
) -> None:
    """
    Deletes configs by key.
    """
    logger.info("Finding storage config with key '{}'", config_key)

    storage_config: Optional[StorageConfig] = StorageConfig.get_by(
        db, field="key", value=config_key
    )
    if not storage_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No configuration with key {config_key}.",
        )
    if storage_config.is_default:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Default storage configurations cannot be deleted.",
        )

    logger.info("Deleting storage config with key '{}'", config_key)
    storage_config.delete(db)


@router.put(
    STORAGE_DEFAULT,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_CREATE_OR_UPDATE])],
    response_model=StorageDestinationResponse,
)
def put_default_config(
    *,
    db: Session = Depends(deps.get_db),
    incoming_storage_config: StorageDestinationBase,
) -> StorageConfig:
    """
    Create or update the default storage configuration for the given storage type
    """
    logger.info(
        "Starting upsert for default storage of type '{}'", incoming_storage_config.type
    )

    incoming_data = incoming_storage_config.dict()
    existing_default = get_default_storage_config_by_type(
        db, incoming_storage_config.type
    )
    if existing_default:
        # take the key of the existing default and add that to the incoming data, to ensure we overwrite the same record
        incoming_data["key"] = existing_default.key
    else:
        # set a name for our config if we're creating a new default
        incoming_data["name"] = default_storage_config_name(
            incoming_storage_config.type  # type: ignore
        )

    # since we're setting the default storage config for the given type, `is_default` MUST be set to `True`
    incoming_data["is_default"] = True

    try:
        storage_config = StorageConfig.create_or_update(db=db, data=incoming_data)
        return storage_config
    except KeyOrNameAlreadyExists as exc:
        logger.warning(
            "Create/update failed for default config update for storage type {}: {}",
            incoming_storage_config.type,
            exc,
        )
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=exc.args[0])
    except Exception as exc:
        logger.warning(
            "Create/update failed for default config update for storage type {}: {}",
            incoming_storage_config.type,
            Pii(str(exc)),
        )
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating or updating storage config.",
        )


@router.put(
    STORAGE_DEFAULT_SECRETS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_CREATE_OR_UPDATE])],
    response_model=TestStatusMessage,
)
def put_default_config_secrets(
    storage_type: StorageType,
    *,
    db: Session = Depends(deps.get_db),
    unvalidated_storage_secrets: possible_storage_secrets,
    verify: Optional[bool] = True,
) -> TestStatusMessage:
    """
    Add or update secrets for the default storage config of the given type
    """
    logger.info("Finding default config of storage type '{}'", storage_type.value)
    storage_config = get_default_storage_config_by_type(db, storage_type)
    if not storage_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No default configuration found for storage type {storage_type.value}.",
        )
    try:
        secrets_schema = get_schema_for_secrets(
            storage_type=storage_config.type,
            secrets=unvalidated_storage_secrets,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.args[0],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.args[0],
        )

    logger.info(
        "Updating storage config secrets for default config of storage type '{}'",
        storage_type.value,
    )
    try:
        storage_config.set_secrets(db=db, storage_secrets=secrets_schema.dict())  # type: ignore
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.args[0],
        )

    msg = f"Secrets updated for default config of storage type: {storage_type.value}."
    if verify:
        status = secrets_are_valid(secrets_schema, storage_config.type)
        if status:
            logger.info(
                "Storage secrets are valid for default config of storage type '{}'",
                storage_type.value,
            )
        else:
            logger.warning(
                "Storage secrets are invalid for default config of storage type '{}'",
                storage_type.value,
            )

        return TestStatusMessage(
            msg=msg,
            test_status=ConnectionTestStatus.succeeded
            if status
            else ConnectionTestStatus.failed,
        )

    return TestStatusMessage(msg=msg, test_status=None)


@router.get(
    STORAGE_DEFAULT,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_READ])],
    response_model=Page[StorageDestinationResponse],
)
def get_default_configs(
    *, db: Session = Depends(deps.get_db), params: Params = Depends()
) -> AbstractPage[StorageConfig]:
    """
    Retrieves default configs for each storage types.
    """
    logger.info(
        "Finding default storage configurations with pagination params {}", params
    )
    return paginate(
        db.query(StorageConfig)
        .filter_by(is_default=True)
        .order_by(StorageConfig.created_at.desc()),
        params=params,
    )


@router.get(
    STORAGE_DEFAULT_BY_TYPE,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_READ])],
    response_model=StorageDestinationResponse,
)
def get_default_config_by_type(
    storage_type: StorageType, *, db: Session = Depends(deps.get_db)
) -> Optional[StorageConfig]:
    """
    Retrieves default config for given storage type.
    """
    logger.info("Finding default config for storage type '{}'", storage_type.value)
    storage_config = get_default_storage_config_by_type(db, storage_type)
    if not storage_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No default config for storage type {storage_type.value}.",
        )
    return storage_config


@router.get(
    STORAGE_ACTIVE_DEFAULT,
    dependencies=[Security(verify_oauth_client, scopes=[STORAGE_READ])],
    response_model=StorageDestinationResponse,
)
def get_active_default_config(
    *, db: Session = Depends(deps.get_db)
) -> Optional[StorageConfig]:
    """
    Retrieves the active default storage config.
    """
    logger.info("Finding active default storage config")
    storage_config = get_active_default_storage_config(db)
    if not storage_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No active default storage config found.",
        )
    return storage_config
