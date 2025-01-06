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
from fides.api.api.v1.endpoints.policy_endpoints import get_policy_or_error
from fides.api.common_exceptions import KeyOrNameAlreadyExists, WebhookOrderException
from fides.api.db.base_class import get_key_from_data
from fides.api.models.policy import (
    Policy,
    PolicyPostWebhook,
    PolicyPreWebhook,
    WebhookTypes,
)
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas import policy_webhooks as schemas
from fides.api.schemas.policy_webhooks import PolicyWebhookDeleteResponse
from fides.api.util.api_router import APIRouter
from fides.api.util.connection_util import get_connection_config_or_error
from fides.common.api import scope_registry as scopes
from fides.common.api.v1 import urn_registry as urls

router = APIRouter(tags=["DSR Policy Webhooks"], prefix=urls.V1_URL_PREFIX)


@router.get(
    urls.POLICY_WEBHOOKS_PRE,
    status_code=HTTP_200_OK,
    response_model=Page[schemas.PolicyWebhookResponse],
    dependencies=[Security(verify_oauth_client, scopes=[scopes.WEBHOOK_READ])],
)
def get_policy_pre_execution_webhooks(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    params: Params = Depends(),
) -> AbstractPage[PolicyPreWebhook]:
    """
    Return a paginated list of all Pre-Execution Webhooks that will
    run in order for the Policy **before** a Privacy Request is executed.
    """
    policy = get_policy_or_error(db, policy_key)

    logger.debug(
        "Finding all Pre-Execution Webhooks for Policy '{}' with pagination params '{}'",
        policy.key,
        params,
    )
    return paginate(policy.pre_execution_webhooks.order_by("order"), params=params)  # type: ignore[attr-defined]


@router.get(
    urls.POLICY_WEBHOOKS_POST,
    status_code=HTTP_200_OK,
    response_model=Page[schemas.PolicyWebhookResponse],
    dependencies=[Security(verify_oauth_client, scopes=[scopes.WEBHOOK_READ])],
)
def get_policy_post_execution_webhooks(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    params: Params = Depends(),
) -> AbstractPage[PolicyPostWebhook]:
    """
    Return a paginated list of all Post-Execution Webhooks that will run in order for the Policy **after** a
    Privacy Request is executed.
    """
    policy = get_policy_or_error(db, policy_key)

    logger.debug(
        "Finding all Post-Execution Webhooks for Policy '{}' with pagination params '{}'",
        policy.key,
        params,
    )
    return paginate(policy.post_execution_webhooks.order_by("order"), params=params)  # type: ignore[attr-defined]


def put_webhooks(
    webhook_cls: WebhookTypes,
    policy_key: FidesKey,
    db: Session = Depends(deps.get_db),
    webhooks: List[schemas.PolicyWebhookCreate] = Body(...),
) -> List[WebhookTypes]:
    """
    Helper method to PUT pre-execution or post-execution policy webhooks.

    Creates/updates webhooks with the same "order" in which they arrived. This endpoint is all-or-nothing.
    Either all webhooks should be created/updated or none should be updated. Deletes any webhooks not present
    in the request body.
    """
    policy = get_policy_or_error(db, policy_key)

    keys = [
        get_key_from_data(webhook.model_dump(mode="json"), type(webhook_cls).__name__)
        for webhook in webhooks
    ]
    names = [webhook.name for webhook in webhooks]
    # Because resources are dependent on each other for order, we want to make sure that we don't have multiple
    # resources in the request that actually point to the same object.
    if len(keys) != len(set(keys)) or len(names) != len(set(names)):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Check request body: there are multiple webhooks whose keys or names resolve to the same value.",
        )

    staged_webhooks = []  # Webhooks will be committed at the end
    for webhook_index, schema in enumerate(webhooks):
        connection_config = get_connection_config_or_error(
            db, schema.connection_config_key
        )

        try:
            webhook = webhook_cls.create_or_update(
                db=db,
                data={
                    "key": schema.key,
                    "name": schema.name,
                    "policy_id": policy.id,
                    "connection_config_id": connection_config.id,
                    "direction": schema.direction,
                    "order": webhook_index,  # Add in the order they arrived in the request
                },
            )
            staged_webhooks.append(webhook)
        except KeyOrNameAlreadyExists as exc:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=exc.args[0],
            )

    staged_webhook_keys = [webhook.key for webhook in staged_webhooks]
    webhooks_to_remove = getattr(
        policy, f"{webhook_cls.prefix}_execution_webhooks"
    ).filter(
        webhook_cls.key.not_in(staged_webhook_keys)  # type: ignore
    )

    if webhooks_to_remove.count():
        logger.info(
            "Removing {}-Execution Webhooks from Policy '{}' that were not included in request: {}",
            webhook_cls.prefix.capitalize(),
            policy.key,
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


@router.put(
    urls.POLICY_WEBHOOKS_PRE,
    status_code=HTTP_200_OK,
    dependencies=[
        Security(verify_oauth_client, scopes=[scopes.WEBHOOK_CREATE_OR_UPDATE])
    ],
    response_model=List[schemas.PolicyWebhookResponse],
)
def create_or_update_pre_execution_webhooks(
    *,
    policy_key: FidesKey,
    db: Session = Depends(deps.get_db),
    webhooks: Annotated[List[schemas.PolicyWebhookCreate], Field(max_length=50)],  # type: ignore
) -> List[PolicyPreWebhook]:
    """
    Create or update the list of Policy Pre-Execution Webhooks that run **before** query execution.

    All webhooks must be included in the request in the desired order. Any missing webhooks
    from the request body will be removed.
    """
    return put_webhooks(PolicyPreWebhook, policy_key, db, webhooks)  # type: ignore


@router.put(
    urls.POLICY_WEBHOOKS_POST,
    status_code=HTTP_200_OK,
    dependencies=[
        Security(verify_oauth_client, scopes=[scopes.WEBHOOK_CREATE_OR_UPDATE])
    ],
    response_model=List[schemas.PolicyWebhookResponse],
)
def create_or_update_post_execution_webhooks(
    *,
    policy_key: FidesKey,
    db: Session = Depends(deps.get_db),
    webhooks: Annotated[List[schemas.PolicyWebhookCreate], Field(max_length=50)],  # type: ignore
) -> List[PolicyPostWebhook]:
    """
    Create or update the list of Policy Post-Execution Webhooks that run **after** query execution.

    All webhooks must be included in the request in the desired order. Any missing webhooks
    from the request body will be removed.
    """
    return put_webhooks(PolicyPostWebhook, policy_key, db, webhooks)  # type: ignore


def get_policy_webhook_or_error(
    db: Session,
    policy: Policy,
    webhook_key: FidesKey,
    webhook_cls: WebhookTypes,
) -> WebhookTypes:
    """Helper method to load a Pre-Execution or Post-Execution Policy Webhook or 404

    Also verifies that the webhook belongs to the given Policy.
    """
    logger.debug(
        "Finding {}-Execution Webhook with key '{}' for Policy '{}'",
        webhook_cls.prefix.capitalize(),
        webhook_key,
        policy.key,
    )
    loaded_webhook = webhook_cls.filter(
        db=db,
        conditions=(
            (webhook_cls.policy_id == policy.id) & (webhook_cls.key == webhook_key)
        ),
    ).first()
    if not loaded_webhook:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No {webhook_cls.prefix.capitalize()}-Execution Webhook found for key '{webhook_key}' on Policy '{policy.key}'.",
        )
    return loaded_webhook


@router.get(
    urls.POLICY_PRE_WEBHOOK_DETAIL,
    status_code=HTTP_200_OK,
    response_model=schemas.PolicyWebhookResponse,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.WEBHOOK_READ])],
)
def get_policy_pre_execution_webhook(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    pre_webhook_key: FidesKey,
) -> PolicyPreWebhook:
    """
    Loads the given Pre-Execution Webhook on the Policy
    """
    policy = get_policy_or_error(db, policy_key)
    return get_policy_webhook_or_error(db, policy, pre_webhook_key, PolicyPreWebhook)  # type: ignore


@router.get(
    urls.POLICY_POST_WEBHOOK_DETAIL,
    status_code=HTTP_200_OK,
    response_model=schemas.PolicyWebhookResponse,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.WEBHOOK_READ])],
)
def get_policy_post_execution_webhook(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    post_webhook_key: FidesKey,
) -> PolicyPostWebhook:
    """
    Loads the given Post-Execution Webhook on the Policy
    """
    policy = get_policy_or_error(db, policy_key)
    return get_policy_webhook_or_error(db, policy, post_webhook_key, PolicyPostWebhook)  # type: ignore


def _patch_webhook(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    webhook_key: FidesKey,
    webhook_body: schemas.PolicyWebhookUpdate = Body(...),
    webhook_cls: WebhookTypes,
) -> schemas.PolicyWebhookUpdateResponse:
    """Helper method for PATCHing a single webhook, either Pre-Execution or Post-Execution

    If the order is updated, this will affect the order of other webhooks.
    """
    policy = get_policy_or_error(db, policy_key)
    loaded_webhook = get_policy_webhook_or_error(db, policy, webhook_key, webhook_cls)
    data = webhook_body.model_dump(exclude_none=True)

    if data.get("connection_config_key"):
        connection_config = get_connection_config_or_error(
            db, data.get("connection_config_key")  # type: ignore
        )
        data["connection_config_id"] = connection_config.id

    # Removing index from incoming data - we'll set this at the end.
    index = data.pop("order", None)

    try:
        logger.info(
            "Updating {}-Execution Webhook with key '{}' on Policy '{}' ",
            webhook_cls.prefix.capitalize(),
            webhook_key,
            policy_key,
        )
        loaded_webhook.update(db, data=data)
    except KeyOrNameAlreadyExists as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.args[0],
        )

    if index is not None and index != loaded_webhook.order:
        logger.info(
            "Reordering {}-Execution Webhooks for Policy '{}'",
            webhook_cls.prefix.capitalize(),
            policy_key,
        )
        try:
            loaded_webhook.reorder_related_webhooks(db=db, new_index=index)
        except WebhookOrderException as exc:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=exc.args[0],
            )

        return schemas.PolicyWebhookUpdateResponse(
            resource=loaded_webhook,
            new_order=[
                webhook
                for webhook in getattr(
                    policy, f"{webhook_cls.prefix}_execution_webhooks"
                ).order_by(webhook_cls.order)
            ],
        )

    # Policy Webhooks are not committed by default, so we commit at the end.
    db.commit()
    return schemas.PolicyWebhookUpdateResponse(resource=loaded_webhook, new_order=[])


@router.patch(
    urls.POLICY_PRE_WEBHOOK_DETAIL,
    status_code=HTTP_200_OK,
    dependencies=[
        Security(verify_oauth_client, scopes=[scopes.WEBHOOK_CREATE_OR_UPDATE])
    ],
    response_model=schemas.PolicyWebhookUpdateResponse,
)
def update_pre_execution_webhook(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    pre_webhook_key: FidesKey,
    webhook_body: schemas.PolicyWebhookUpdate = Body(...),
) -> schemas.PolicyWebhookUpdateResponse:
    """PATCH a single Policy Pre-Execution Webhook that runs **prior** to executing the Privacy Request.

    Note that updates to the webhook's "order" can affect the order of the other pre-execution webhooks.
    """
    return _patch_webhook(
        db=db,
        policy_key=policy_key,
        webhook_key=pre_webhook_key,
        webhook_body=webhook_body,
        webhook_cls=PolicyPreWebhook,  # type: ignore
    )


@router.patch(
    urls.POLICY_POST_WEBHOOK_DETAIL,
    status_code=HTTP_200_OK,
    dependencies=[
        Security(verify_oauth_client, scopes=[scopes.WEBHOOK_CREATE_OR_UPDATE])
    ],
    response_model=schemas.PolicyWebhookUpdateResponse,
)
def update_post_execution_webhook(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    post_webhook_key: FidesKey,
    webhook_body: schemas.PolicyWebhookUpdate = Body(...),
) -> schemas.PolicyWebhookUpdateResponse:
    """PATCH a single Policy Post-Execution Webhook that runs **after** executing the Privacy Request.

    Note that updates to the webhook's "order" can affect the order of the other post-execution webhooks.
    """
    return _patch_webhook(
        db=db,
        policy_key=policy_key,
        webhook_key=post_webhook_key,
        webhook_body=webhook_body,
        webhook_cls=PolicyPostWebhook,  # type: ignore
    )


def delete_webhook(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    webhook_key: FidesKey,
    webhook_cls: WebhookTypes,
) -> PolicyWebhookDeleteResponse:
    """Handles deleting Pre- or Post-Execution Policy Webhooks. Related webhooks are reordered as necessary"""
    policy = get_policy_or_error(db, policy_key)
    loaded_webhook = get_policy_webhook_or_error(db, policy, webhook_key, webhook_cls)
    total_webhook_count = (
        getattr(policy, f"{webhook_cls.prefix}_execution_webhooks").count() - 1
    )
    reordering = total_webhook_count != loaded_webhook.order

    if reordering:
        # Move the webhook to the end and shuffle other webhooks
        logger.info(
            "Reordering {}-Execution Webhooks for Policy '{}'",
            webhook_cls.prefix.capitalize(),
            policy_key,
        )
        loaded_webhook.reorder_related_webhooks(db=db, new_index=total_webhook_count)

    logger.info(
        "Deleting {}-Execution Webhook with key '{}' off of Policy '{}'",
        webhook_cls.prefix.capitalize(),
        webhook_key,
        policy_key,
    )
    loaded_webhook.delete(db=db)
    return PolicyWebhookDeleteResponse(
        new_order=(
            [
                webhook
                for webhook in getattr(
                    policy, f"{webhook_cls.prefix}_execution_webhooks"
                ).order_by(webhook_cls.order)
            ]
            if reordering
            else []
        )
    )


@router.delete(
    urls.POLICY_PRE_WEBHOOK_DETAIL,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.WEBHOOK_DELETE])],
    response_model=schemas.PolicyWebhookDeleteResponse,
)
def delete_pre_execution_webhook(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    pre_webhook_key: FidesKey,
) -> schemas.PolicyWebhookDeleteResponse:
    """Delete the Pre-Execution Webhook from the Policy and reorder remaining webhooks as necessary."""
    return delete_webhook(
        db=db,
        policy_key=policy_key,
        webhook_key=pre_webhook_key,
        webhook_cls=PolicyPreWebhook,  # type: ignore
    )


@router.delete(
    urls.POLICY_POST_WEBHOOK_DETAIL,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.WEBHOOK_DELETE])],
    response_model=schemas.PolicyWebhookDeleteResponse,
)
def delete_post_execution_webhook(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    post_webhook_key: FidesKey,
) -> schemas.PolicyWebhookDeleteResponse:
    """Delete the Post-Execution Webhook from the Policy and reorder remaining webhooks as necessary."""
    return delete_webhook(
        db=db,
        policy_key=policy_key,
        webhook_key=post_webhook_key,
        webhook_cls=PolicyPostWebhook,  # type: ignore
    )
