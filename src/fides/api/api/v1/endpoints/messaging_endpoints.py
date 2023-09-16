from typing import Dict, List, Optional

from fastapi import Depends, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.validation import FidesKey
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

from fides.api.api import deps
from fides.api.common_exceptions import (
    MessageDispatchException,
    MessagingConfigNotFoundException,
)
from fides.api.models.messaging import (
    MessagingConfig,
    default_messaging_config_key,
    default_messaging_config_name,
    get_schema_for_secrets,
)
from fides.api.models.messaging_template import (
    DEFAULT_MESSAGING_TEMPLATES,
    MessagingTemplate,
)
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.api import BulkUpdateFailed
from fides.api.schemas.messaging.messaging import (
    BulkPutMessagingTemplateResponse,
    MessagingActionType,
    MessagingConfigRequest,
    MessagingConfigRequestBase,
    MessagingConfigResponse,
    MessagingConfigStatus,
    MessagingConfigStatusMessage,
    MessagingServiceType,
    MessagingTemplateRequest,
    MessagingTemplateResponse,
    TestMessagingStatusMessage,
)
from fides.api.schemas.messaging.messaging_secrets_docs_only import (
    possible_messaging_secrets,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.message_dispatch_service import dispatch_message
from fides.api.service.messaging.messaging_crud_service import (
    create_or_update_messaging_config,
    delete_messaging_config,
    get_all_messaging_templates,
    get_messaging_config_by_key,
    update_messaging_config,
)
from fides.api.util.api_router import APIRouter
from fides.api.util.logger import Pii
from fides.common.api.scope_registry import (
    MESSAGING_CREATE_OR_UPDATE,
    MESSAGING_DELETE,
    MESSAGING_READ,
    MESSAGING_TEMPLATE_UPDATE,
)
from fides.common.api.v1.urn_registry import (
    MESSAGING_ACTIVE_DEFAULT,
    MESSAGING_BY_KEY,
    MESSAGING_CONFIG,
    MESSAGING_DEFAULT,
    MESSAGING_DEFAULT_BY_TYPE,
    MESSAGING_DEFAULT_SECRETS,
    MESSAGING_SECRETS,
    MESSAGING_STATUS,
    MESSAGING_TEMPLATES,
    MESSAGING_TEST,
    V1_URL_PREFIX,
)
from fides.config.config_proxy import ConfigProxy

router = APIRouter(tags=["Messaging"], prefix=V1_URL_PREFIX)


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
    config_key: FidesKey,
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


# this needs to come before other `/default/{messaging_type}` routes so that `/status`
# isn't picked up as a path param
@router.get(
    MESSAGING_ACTIVE_DEFAULT,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_READ])],
    response_model=MessagingConfigResponse,
)
def get_active_default_config(*, db: Session = Depends(deps.get_db)) -> MessagingConfig:
    """
    Retrieves the active default messaging config.
    """
    logger.info("Finding active default messaging config")
    try:
        messaging_config = MessagingConfig.get_active_default(db)
    except ValueError:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid notification_service_type configured.",
        )
    if not messaging_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No active default messaging config found.",
        )
    return messaging_config


# this needs to come before other `/default/{messaging_type}` routes so that `/status`
# isn't picked up as a path param
@router.get(
    MESSAGING_STATUS,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_READ])],
    response_model=MessagingConfigStatusMessage,
    responses={
        HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "config_status": "configured",
                        "detail": "Active default messaging service of type mailgun is fully configured",
                    }
                }
            }
        }
    },
)
def get_messaging_status(
    *, db: Session = Depends(deps.get_db)
) -> MessagingConfigStatusMessage:
    """
    Determines the status of the active default messaging config
    """
    logger.info("Determining active default messaging config status")

    # confirm an active default messaging config is present
    messaging_config = MessagingConfig.get_active_default(db)
    if not messaging_config:
        return MessagingConfigStatusMessage(
            config_status=MessagingConfigStatus.not_configured,
            detail="No active default messaging configuration found",
        )

    try:
        details = messaging_config.details
        MessagingConfigRequestBase.validate_details_schema(
            messaging_config.service_type, details
        )
    except Exception as e:
        logger.error(f"Invalid or unpopulated details on {messaging_config.service_type.value} messaging configuration: {Pii(str(e))}")  # type: ignore
        return MessagingConfigStatusMessage(
            config_status=MessagingConfigStatus.not_configured,
            detail=f"Invalid or unpopulated details on {messaging_config.service_type.value} messaging configuration",  # type: ignore
        )

    # confirm secrets are present and pass validation
    secrets = messaging_config.secrets
    if not secrets:
        return MessagingConfigStatusMessage(
            config_status=MessagingConfigStatus.not_configured,
            detail=f"No secrets found for {messaging_config.service_type.value} messaging configuration",  # type: ignore
        )
    try:
        get_schema_for_secrets(
            service_type=messaging_config.service_type,  # type: ignore
            secrets=secrets,
        )
    except (ValueError, KeyError) as e:
        logger.error(f"Invalid secrets found on {messaging_config.service_type.value} messaging configuration: {Pii(str(e))}")  # type: ignore
        return MessagingConfigStatusMessage(
            config_status=MessagingConfigStatus.not_configured,
            detail=f"Invalid secrets found on {messaging_config.service_type.value} messaging configuration",  # type: ignore
        )

    return MessagingConfigStatusMessage(
        config_status=MessagingConfigStatus.configured,
        detail=f"Active default messaging service of type {messaging_config.service_type.value} is fully configured",  # type: ignore
    )


@router.put(
    MESSAGING_DEFAULT,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_CREATE_OR_UPDATE])],
    response_model=MessagingConfigResponse,
)
def put_default_config(
    *,
    db: Session = Depends(deps.get_db),
    messaging_config: MessagingConfigRequestBase,
) -> Optional[MessagingConfigResponse]:
    """
    Updates default messaging config for given service type.
    """
    logger.info(
        "Starting upsert for default messaging config of type '{}'",
        messaging_config.service_type,
    )
    incoming_data = messaging_config.dict()
    existing_default = MessagingConfig.get_by_type(db, messaging_config.service_type)
    if existing_default:
        # take the key of the existing default and add that to the incoming data, to ensure we overwrite the same record
        incoming_data["key"] = existing_default.key
        incoming_data["name"] = existing_default.name
    else:
        # set a key and name for our config if we're creating a new default
        incoming_data["name"] = default_messaging_config_name(
            messaging_config.service_type.value
        )
        incoming_data["key"] = default_messaging_config_key(
            messaging_config.service_type.value
        )
    return create_or_update_messaging_config(
        db, MessagingConfigRequest(**incoming_data)
    )


@router.put(
    MESSAGING_DEFAULT_SECRETS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_CREATE_OR_UPDATE])],
    response_model=TestMessagingStatusMessage,
)
def put_default_config_secrets(
    service_type: MessagingServiceType,
    *,
    db: Session = Depends(deps.get_db),
    unvalidated_messaging_secrets: possible_messaging_secrets,
) -> TestMessagingStatusMessage:
    messaging_config = MessagingConfig.get_by_type(db, service_type=service_type)
    if not messaging_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No default messaging config found of type '{service_type}'",
        )
    return update_config_secrets(db, messaging_config, unvalidated_messaging_secrets)


@router.put(
    MESSAGING_SECRETS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_CREATE_OR_UPDATE])],
    response_model=TestMessagingStatusMessage,
)
def put_config_secrets(
    config_key: FidesKey,
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
    return update_config_secrets(db, messaging_config, unvalidated_messaging_secrets)


def update_config_secrets(
    db: Session,
    messaging_config: MessagingConfig,
    unvalidated_messaging_secrets: possible_messaging_secrets,
) -> TestMessagingStatusMessage:
    try:
        secrets_schema = get_schema_for_secrets(
            service_type=messaging_config.service_type,  # type: ignore
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
        "Updating messaging config secrets for config with key '{}'",
        messaging_config.key,
    )
    try:
        messaging_config.set_secrets(db=db, messaging_secrets=secrets_schema.dict())  # type: ignore
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.args[0],
        )
    msg = f"Secrets updated for MessagingConfig with key: {messaging_config.key}."
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
    config_key: FidesKey, *, db: Session = Depends(deps.get_db)
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


@router.get(
    MESSAGING_DEFAULT_BY_TYPE,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_READ])],
    response_model=MessagingConfigResponse,
)
def get_default_config_by_type(
    service_type: MessagingServiceType, *, db: Session = Depends(deps.get_db)
) -> MessagingConfig:
    """
    Retrieves default config for messaging service by type.
    """
    logger.info("Finding default messaging config of type '{}'", service_type)

    messaging_config = MessagingConfig.get_by_type(db, service_type)
    if not messaging_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No default messaging config found of type '{service_type}'",
        )
    return messaging_config


@router.delete(
    MESSAGING_BY_KEY,
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_DELETE])],
)
def delete_config_by_key(
    config_key: FidesKey, *, db: Session = Depends(deps.get_db)
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


@router.post(
    MESSAGING_TEST,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_CREATE_OR_UPDATE])],
    response_model=Dict[str, str],
    responses={
        HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "details": "Test message successfully sent",
                    }
                }
            }
        }
    },
)
def send_test_message(
    message_info: Identity,
    db: Session = Depends(deps.get_db),
    config_proxy: ConfigProxy = Depends(deps.get_config_proxy),
) -> Dict[str, str]:
    """Sends a test message."""
    try:
        dispatch_message(
            db,
            action_type=MessagingActionType.TEST_MESSAGE,
            to_identity=message_info,
            service_type=config_proxy.notifications.notification_service_type,
        )
    except MessageDispatchException as e:
        raise HTTPException(
            status_code=400, detail=f"There was an error sending the test message: {e}"
        )
    return {"details": "Test message successfully sent"}


@router.get(
    MESSAGING_TEMPLATES,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_TEMPLATE_UPDATE])],
    response_model=List[MessagingTemplateResponse],
)
def get_messaging_templates(
    *, db: Session = Depends(deps.get_db)
) -> List[MessagingTemplateResponse]:
    """Returns the available messaging templates, augments the models with labels to be used in the UI."""
    return [
        MessagingTemplateResponse(
            key=template.key,
            content=template.content,
            label=DEFAULT_MESSAGING_TEMPLATES.get(template.key, {}).get("label", None),
        )
        for template in get_all_messaging_templates(db=db)
    ]


@router.put(
    MESSAGING_TEMPLATES,
    dependencies=[Security(verify_oauth_client, scopes=[MESSAGING_TEMPLATE_UPDATE])],
)
def update_messaging_templates(
    templates: List[MessagingTemplateRequest], *, db: Session = Depends(deps.get_db)
) -> BulkPutMessagingTemplateResponse:
    """Updates the messaging templates and reverts empty subject or body values to the default values."""

    succeeded = []
    failed = []

    for template in templates:
        key = template.key
        content = template.content

        try:
            default_template = DEFAULT_MESSAGING_TEMPLATES.get(key)
            if not default_template:
                raise ValueError("Invalid template key.")

            content["subject"] = (
                content["subject"] or default_template["content"]["subject"]
            )
            content["body"] = content["body"] or default_template["content"]["body"]

            MessagingTemplate.create_or_update(
                db, data={"key": key, "content": content}
            )

            succeeded.append(
                MessagingTemplateResponse(
                    key=key,
                    content=content,
                    label=default_template.get("label"),
                )
            )

        except ValueError as e:
            failed.append(BulkUpdateFailed(message=str(e), data=template))
        except Exception:
            failed.append(
                BulkUpdateFailed(
                    message="Unexpected error updating template.", data=template
                )
            )

    return BulkPutMessagingTemplateResponse(succeeded=succeeded, failed=failed)
