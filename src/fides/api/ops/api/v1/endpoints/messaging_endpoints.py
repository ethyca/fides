from typing import Optional

from fastapi import Depends, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fides.api.ops.api import deps
from fides.api.ops.api.v1.scope_registry import (
    MESSAGING_CREATE_OR_UPDATE,
    MESSAGING_DELETE,
    MESSAGING_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    MESSAGING_BY_KEY,
    MESSAGING_CONFIG,
    MESSAGING_SECRETS,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import MessagingConfigNotFoundException
from fides.api.ops.models.messaging import MessagingConfig, get_schema_for_secrets
from fides.api.ops.schemas.messaging.messaging import (
    MessagingConfigRequest,
    MessagingConfigResponse,
    TestMessagingStatusMessage,
)
from fides.api.ops.schemas.messaging.messaging_secrets_docs_only import (
    possible_messaging_secrets,
)
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.service.messaging.messaging_crud_service import (
    create_or_update_messaging_config,
    delete_messaging_config,
    get_messaging_config_by_key,
    update_messaging_config,
)
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.logger import Pii
from fides.api.ops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["messaging"], prefix=V1_URL_PREFIX)


@router.post(
    MESSAGING_CONFIG,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_CREATE_OR_UPDATE])],
    response_model=MessagingConfigResponse,
)
def post_config(
    *,
    db: Session = Depends(deps.get_db),
    messaging_config: MessagingConfigRequest,
) -> MessagingConfigResponse:
    """
    Given a messaging config, create corresponding MessagingConfig object, provided no config already exists
    """

    try:
        return create_or_update_messaging_config(db=db, config=messaging_config)
    except ValueError as e:
        logger.warning(
            "Create failed for messaging config {}: {}",
            messaging_config.key,
            Pii(str(e)),
        )
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Config with key {messaging_config.key} failed to be added: {e}",
        )
    except Exception as exc:
        logger.warning(
            "Create failed for messaging config {}: {}",
            messaging_config.key,
            Pii(str(exc)),
        )
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Config with key {messaging_config.key} failed to be added: {exc}",
        )


@router.patch(
    MESSAGING_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_CREATE_OR_UPDATE])],
    response_model=MessagingConfigResponse,
)
def patch_config_by_key(
    config_key: FidesOpsKey,
    *,
    db: Session = Depends(deps.get_db),
    messaging_config: MessagingConfigRequest,
) -> Optional[MessagingConfigResponse]:
    """
    Updates config for messaging by key, provided config with key can be found.
    """
    try:
        return update_messaging_config(db=db, key=config_key, config=messaging_config)
    except MessagingConfigNotFoundException:
        logger.warning("No messaging config found with key {}", config_key)
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No messaging config found with key {config_key}",
        )
    except Exception as exc:
        logger.warning(
            "Patch failed for messaging config {}: {}",
            messaging_config.key,
            Pii(str(exc)),
        )
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Config with key {messaging_config.key} failed to be added",
        )


@router.put(
    MESSAGING_SECRETS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_CREATE_OR_UPDATE])],
    response_model=TestMessagingStatusMessage,
)
def put_config_secrets(
    config_key: FidesOpsKey,
    *,
    db: Session = Depends(deps.get_db),
    unvalidated_messaging_secrets: possible_messaging_secrets,
) -> TestMessagingStatusMessage:
    """
    Add or update secrets for messaging config.
    """
    logger.info("Finding messaging config with key '{}'", config_key)
    messaging_config = MessagingConfig.get_by(db=db, field="key", value=config_key)
    if not messaging_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No messaging configuration with key {config_key}.",
        )

    try:
        secrets_schema = get_schema_for_secrets(
            service_type=messaging_config.service_type,
            secrets=unvalidated_messaging_secrets,
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
        "Updating messaging config secrets for config with key '{}'", config_key
    )
    try:
        messaging_config.set_secrets(db=db, messaging_secrets=secrets_schema.dict())
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.args[0],
        )
    msg = f"Secrets updated for MessagingConfig with key: {config_key}."
    # todo- implement test status for messaging service
    return TestMessagingStatusMessage(msg=msg, test_status=None)


@router.get(
    MESSAGING_CONFIG,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_READ])],
    response_model=Page[MessagingConfigResponse],
)
def get_configs(
    *, db: Session = Depends(deps.get_db), params: Params = Depends()
) -> AbstractPage[MessagingConfig]:
    """
    Retrieves configs for messaging.
    """
    logger.info(
        "Finding all messaging configurations with pagination params {}", params
    )
    return paginate(
        MessagingConfig.query(db=db).order_by(MessagingConfig.created_at.desc()),
        params=params,
    )


@router.get(
    MESSAGING_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_READ])],
    response_model=MessagingConfigResponse,
)
def get_config_by_key(
    config_key: FidesOpsKey, *, db: Session = Depends(deps.get_db)
) -> MessagingConfigResponse:
    """
    Retrieves configs for messaging service by key.
    """
    logger.info("Finding messaging config with key '{}'", config_key)

    try:
        return get_messaging_config_by_key(db=db, key=config_key)
    except MessagingConfigNotFoundException as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.delete(
    MESSAGING_BY_KEY,
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_DELETE])],
)
def delete_config_by_key(
    config_key: FidesOpsKey, *, db: Session = Depends(deps.get_db)
) -> None:
    """
    Deletes messaging configs by key.
    """
    try:
        delete_messaging_config(db=db, key=config_key)
    except MessagingConfigNotFoundException as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=e.message,
        )
