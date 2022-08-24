import logging
from typing import Optional

from fastapi import Depends, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
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
    EMAIL_CREATE_OR_UPDATE,
    EMAIL_DELETE,
    EMAIL_READ,
)
from fides.api.ops.api.v1.urn_registry import (
    EMAIL_BY_KEY,
    EMAIL_CONFIG,
    EMAIL_SECRETS,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import (
    EmailConfigAlreadyExistsException,
    EmailConfigNotFoundException,
)
from fides.api.ops.models.email import EmailConfig, get_schema_for_secrets
from fides.api.ops.schemas.email.email import (
    EmailConfigRequest,
    EmailConfigResponse,
    TestEmailStatusMessage,
)
from fides.api.ops.schemas.email.email_secrets_docs_only import possible_email_secrets
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.service.email.email_crud_service import (
    create_email_config,
    delete_email_config,
    get_email_config_by_key,
    update_email_config,
)
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.logger import Pii
from fides.api.ops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["email"], prefix=V1_URL_PREFIX)
logger = logging.getLogger(__name__)


@router.post(
    EMAIL_CONFIG,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[EMAIL_CREATE_OR_UPDATE])],
    response_model=EmailConfigResponse,
)
def post_config(
    *,
    db: Session = Depends(deps.get_db),
    email_config: EmailConfigRequest,
) -> EmailConfigResponse:
    """
    Given an email config, create corresponding EmailConfig object, provided no config already exists
    """

    try:
        return create_email_config(db=db, config=email_config)
    except EmailConfigAlreadyExistsException as e:
        logger.warning(e.message)
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=e.message)

    except Exception as exc:
        logger.warning(
            "Create failed for email config %s: %s", email_config.key, Pii(str(exc))
        )
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Config with key {email_config.key} failed to be added",
        )


@router.patch(
    EMAIL_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[EMAIL_CREATE_OR_UPDATE])],
    response_model=EmailConfigResponse,
)
def patch_config_by_key(
    config_key: FidesOpsKey,
    *,
    db: Session = Depends(deps.get_db),
    email_config: EmailConfigRequest,
) -> Optional[EmailConfigResponse]:
    """
    Updates config for email by key, provided config with key can be found.
    """
    try:
        return update_email_config(db=db, key=config_key, config=email_config)
    except EmailConfigNotFoundException:
        logger.warning("No email config found with key %s", config_key)
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No email config found with key {config_key}",
        )

    except Exception as exc:
        logger.warning(
            "Patch failed for email config %s: %s", email_config.key, Pii(str(exc))
        )
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Config with key {email_config.key} failed to be added",
        )


@router.put(
    EMAIL_SECRETS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[EMAIL_CREATE_OR_UPDATE])],
    response_model=TestEmailStatusMessage,
)
def put_config_secrets(
    config_key: FidesOpsKey,
    *,
    db: Session = Depends(deps.get_db),
    unvalidated_email_secrets: possible_email_secrets,
) -> TestEmailStatusMessage:
    """
    Add or update secrets for email config.
    """
    logger.info("Finding email config with key '%s'", config_key)
    email_config = EmailConfig.get_by(db=db, field="key", value=config_key)
    if not email_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No email configuration with key {config_key}.",
        )

    try:
        secrets_schema = get_schema_for_secrets(
            service_type=email_config.service_type,
            secrets=unvalidated_email_secrets,
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

    logger.info("Updating email config secrets for config with key '%s'", config_key)
    try:
        email_config.set_secrets(db=db, email_secrets=secrets_schema.dict())
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.args[0],
        )

    msg = f"Secrets updated for EmailConfig with key: {config_key}."
    # todo- implement test status for email service
    return TestEmailStatusMessage(msg=msg, test_status=None)


@router.get(
    EMAIL_CONFIG,
    dependencies=[Security(verify_oauth_client, scopes=[EMAIL_READ])],
    response_model=Page[EmailConfigResponse],
)
def get_configs(
    *, db: Session = Depends(deps.get_db), params: Params = Depends()
) -> AbstractPage[EmailConfig]:
    """
    Retrieves configs for email.
    """
    logger.info("Finding all email configurations with pagination params %s", params)
    return paginate(
        EmailConfig.query(db=db).order_by(EmailConfig.created_at.desc()), params=params
    )


@router.get(
    EMAIL_BY_KEY,
    dependencies=[Security(verify_oauth_client, scopes=[EMAIL_READ])],
    response_model=EmailConfigResponse,
)
def get_config_by_key(
    config_key: FidesOpsKey, *, db: Session = Depends(deps.get_db)
) -> EmailConfigResponse:
    """
    Retrieves configs for email by key.
    """
    logger.info("Finding email config with key '%s'", config_key)

    try:
        return get_email_config_by_key(db=db, key=config_key)
    except EmailConfigNotFoundException as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.delete(
    EMAIL_BY_KEY,
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[Security(verify_oauth_client, scopes=[EMAIL_DELETE])],
)
def delete_config_by_key(
    config_key: FidesOpsKey, *, db: Session = Depends(deps.get_db)
) -> None:
    """
    Deletes email configs by key.
    """
    try:
        delete_email_config(db=db, key=config_key)
    except EmailConfigNotFoundException as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=e.message,
        )
