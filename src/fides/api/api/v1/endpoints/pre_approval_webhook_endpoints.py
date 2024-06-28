from typing import Annotated, List

from fastapi import Body, Depends, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import Field
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.api import deps
from fides.api.common_exceptions import KeyOrNameAlreadyExists
from fides.api.db.base_class import get_key_from_data
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas import pre_approval_webhooks as schemas
from fides.api.util.api_router import APIRouter
from fides.api.util.connection_util import get_connection_config_or_error
from fides.common.api import scope_registry as scopes
from fides.common.api.v1 import urn_registry as urls

router = APIRouter(tags=["Pre Approval Webhooks"], prefix=urls.V1_URL_PREFIX)


@router.get(
    urls.WEBHOOK_PRE_APPROVAL,
    status_code=HTTP_200_OK,
    response_model=Page[schemas.PreApprovalWebhookResponse],
    dependencies=[Security(verify_oauth_client, scopes=[scopes.WEBHOOK_READ])],
)
def get_pre_approval_webhook_list(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
) -> AbstractPage[schemas.PreApprovalWebhookResponse]:
    """
    Return a paginated list of all PreApprovalWebhook records in this system
    """
    logger.info("Finding all pre_approval webhooks with pagination params '{}'", params)
    pre_approval_webhooks = PreApprovalWebhook.query(db=db).order_by(
        PreApprovalWebhook.created_at.desc()
    )
    return paginate(pre_approval_webhooks, params=params)


def get_pre_approval_webhook_or_error(
    db: Session, webhook_key: FidesKey
) -> PreApprovalWebhook:
    """Helper method to load PreApprovalWebhook or throw a 404"""
    logger.info("Finding PreApprovalWebhook with key '{}'", webhook_key)
    pre_approval_webhook = PreApprovalWebhook.get_by(
        db=db, field="key", value=webhook_key
    )
    if not pre_approval_webhook:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No PreApprovalWebhook found for key {webhook_key}.",
        )

    return pre_approval_webhook


@router.get(
    urls.WEBHOOK_PRE_APPROVAL_DETAIL,
    status_code=HTTP_200_OK,
    response_model=schemas.PreApprovalWebhookResponse,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.WEBHOOK_READ])],
)
def get_pre_approval_webhook_detail(
    *,
    db: Session = Depends(deps.get_db),
    webhook_key: FidesKey,
) -> PreApprovalWebhook:
    """
    Loads the given Pre-Approval Webhook by key
    """
    return get_pre_approval_webhook_or_error(db, webhook_key)


@router.put(
    urls.WEBHOOK_PRE_APPROVAL,
    status_code=HTTP_200_OK,
    dependencies=[
        Security(verify_oauth_client, scopes=[scopes.WEBHOOK_CREATE_OR_UPDATE])
    ],
    response_model=List[schemas.PreApprovalWebhookResponse],
)
def create_or_update_pre_execution_webhooks(
    *,
    db: Session = Depends(deps.get_db),
    webhooks: Annotated[List[schemas.PreApprovalWebhookCreate], Field(max_length=50)],  # type: ignore
) -> List[PreApprovalWebhook]:
    """
    Create or update the list of Pre-Approval Webhooks that run as soon as a request is created.
    This endpoint is all-or-nothing.
    Either all webhooks should be created/updated or none should be updated. Deletes any webhooks not present
    in the request body.
    """
    pre_approval_webhooks = PreApprovalWebhook.query(db=db)

    keys = [
        get_key_from_data(webhook.model_dump(mode="json"), PreApprovalWebhook.__name__)
        for webhook in webhooks
    ]
    names = [webhook.name for webhook in webhooks]
    if len(keys) != len(set(keys)) or len(names) != len(set(names)):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Check request body: there are multiple webhooks whose keys or names resolve to the same value.",
        )

    staged_webhooks = []  # Webhooks will be committed at the end
    for schema in webhooks:
        connection_config = get_connection_config_or_error(
            db, schema.connection_config_key
        )
        try:
            webhook = PreApprovalWebhook.create_or_update(
                db=db,
                data={
                    "key": schema.key,
                    "name": schema.name,
                    "connection_config_id": connection_config.id,
                },
            )
            staged_webhooks.append(webhook)
        except KeyOrNameAlreadyExists as exc:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=exc.args[0],
            )

    staged_webhook_keys = [webhook.key for webhook in staged_webhooks]
    webhooks_to_remove = pre_approval_webhooks.filter(
        PreApprovalWebhook.key.not_in(staged_webhook_keys)  # type: ignore
    )

    if webhooks_to_remove.count():
        logger.info(
            "Removing Pre-Approval Webhooks that were not included in request: {}",
            [webhook.key for webhook in webhooks_to_remove],
        )
        webhooks_to_remove.delete()

    logger.info(
        "Creating/updating Policy Pre-Execution Webhooks: {}", staged_webhook_keys
    )
    # Committing to database now, as a last step, once we've verified that all the webhooks
    # in the request are free of issues.
    db.commit()
    return staged_webhooks


@router.patch(
    urls.WEBHOOK_PRE_APPROVAL_DETAIL,
    status_code=HTTP_200_OK,
    dependencies=[
        Security(verify_oauth_client, scopes=[scopes.WEBHOOK_CREATE_OR_UPDATE])
    ],
    response_model=schemas.PreApprovalWebhookResponse,
)
def update_pre_execution_webhook(
    *,
    db: Session = Depends(deps.get_db),
    webhook_key: FidesKey,
    webhook_body: schemas.PreApprovalWebhookUpdate = Body(...),
) -> schemas.PreApprovalWebhookResponse:
    """PATCH a single Pre-Approval Webhook that runs as soon as Privacy Request is created."""

    loaded_webhook = get_pre_approval_webhook_or_error(db, webhook_key)
    data = webhook_body.model_dump(exclude_none=True)

    if data.get("connection_config_key"):
        connection_config = get_connection_config_or_error(
            db, data.get("connection_config_key")  # type: ignore
        )
        data["connection_config_id"] = connection_config.id

    try:
        logger.info(
            "Updating Pre-Approval Webhook with key '{}' ",
            webhook_key,
        )
        loaded_webhook.update(db, data=data)
    except KeyOrNameAlreadyExists as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.args[0],
        )

    # Pre Execution Webhooks are not committed by default, so we commit at the end.
    db.commit()
    return schemas.PreApprovalWebhookResponse(
        connection_config=loaded_webhook.connection_config,
        key=loaded_webhook.key,
        name=loaded_webhook.name,
    )


@router.delete(
    urls.WEBHOOK_PRE_APPROVAL_DETAIL,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.WEBHOOK_DELETE])],
)
def delete_pre_execution_webhook(
    *,
    db: Session = Depends(deps.get_db),
    webhook_key: FidesKey,
) -> None:
    """Delete the Pre-Approval Webhook given webhook key"""
    loaded_webhook = get_pre_approval_webhook_or_error(db, webhook_key)

    logger.info(
        "Deleting Pre-Approval Webhook with key '{}'",
        webhook_key,
    )
    loaded_webhook.delete(db=db)
