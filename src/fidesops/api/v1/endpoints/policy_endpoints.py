import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import conlist
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from fidesops.api import deps
from fidesops.api.v1 import scope_registry as scopes
from fidesops.api.v1 import urn_registry as urls
from fidesops.common_exceptions import (
    DataCategoryNotSupported,
    DrpActionValidationError,
    KeyOrNameAlreadyExists,
    PolicyValidationError,
    RuleTargetValidationError,
    RuleValidationError,
)
from fidesops.models.client import ClientDetail
from fidesops.models.policy import ActionType, Policy, Rule, RuleTarget
from fidesops.models.storage import StorageConfig
from fidesops.schemas import policy as schemas
from fidesops.schemas.api import BulkUpdateFailed
from fidesops.schemas.shared_schemas import FidesOpsKey
from fidesops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["Policy"], prefix=urls.V1_URL_PREFIX)

logger = logging.getLogger(__name__)


@router.get(
    urls.POLICY_LIST,
    status_code=HTTP_200_OK,
    response_model=Page[schemas.PolicyResponse],
    dependencies=[Security(verify_oauth_client, scopes=[scopes.POLICY_READ])],
)
def get_policy_list(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
) -> AbstractPage[Policy]:
    """
    Return a paginated list of all Policy records in this system
    """
    logger.info(f"Finding all policies with pagination params '{params}'")
    policies = Policy.query(db=db).order_by(Policy.created_at.desc())
    return paginate(policies, params=params)


def get_policy_or_error(db: Session, policy_key: FidesOpsKey) -> Policy:
    """Helper method to load Policy or throw a 404"""
    logger.info(f"Finding policy with key '{policy_key}'")
    policy = Policy.get_by(db=db, field="key", value=policy_key)
    if not policy:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Policy found for key {policy_key}.",
        )

    return policy


@router.get(
    urls.POLICY_DETAIL,
    status_code=HTTP_200_OK,
    response_model=schemas.PolicyResponse,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.POLICY_READ])],
)
def get_policy(
    *,
    policy_key: FidesOpsKey,
    db: Session = Depends(deps.get_db),
) -> schemas.PolicyResponse:
    """
    Return a single Policy
    """
    return get_policy_or_error(db, policy_key)


@router.patch(
    urls.POLICY_LIST,
    status_code=HTTP_200_OK,
    response_model=schemas.BulkPutPolicyResponse,
)
def create_or_update_policies(
    *,
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[scopes.POLICY_CREATE_OR_UPDATE],
    ),
    db: Session = Depends(deps.get_db),
    data: conlist(schemas.Policy, max_items=50) = Body(...),  # type: ignore
) -> schemas.BulkPutPolicyResponse:
    """
    Given a list of policy data elements, create or update corresponding Policy objects
    or report failure
    """
    created_or_updated: List[Policy] = []
    failed: List[BulkUpdateFailed] = []
    logger.info(f"Starting bulk upsert for {len(data)} policies")

    for policy_schema in data:
        policy_data: Dict[str, Any] = dict(policy_schema)
        try:
            policy = Policy.create_or_update(
                db=db,
                data={
                    "name": policy_data["name"],
                    "key": policy_data.get("key"),
                    "client_id": client.id,
                    "drp_action": policy_data.get("drp_action"),
                },
            )
        except (
            KeyOrNameAlreadyExists,
            DrpActionValidationError,
            IntegrityError,
        ) as exc:
            logger.warning("Create/update failed for policy: %s", exc)
            failure = {
                "message": exc.args[0],
                "data": policy_data,
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        except PolicyValidationError as exc:
            logger.warning("Create/update failed for policy: %s", exc)
            failure = {
                "message": "This record could not be added because the data provided was invalid.",
                "data": policy_data,
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        else:
            created_or_updated.append(policy)

    return schemas.BulkPutPolicyResponse(
        succeeded=created_or_updated,
        failed=failed,
    )


@router.patch(
    urls.RULE_LIST,
    status_code=HTTP_200_OK,
    response_model=schemas.BulkPutRuleResponse,
)
def create_or_update_rules(
    *,
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[scopes.RULE_CREATE_OR_UPDATE],
    ),
    policy_key: FidesOpsKey,
    db: Session = Depends(deps.get_db),
    input_data: conlist(schemas.RuleCreate, max_items=50) = Body(...),  # type: ignore
) -> schemas.BulkPutRuleResponse:
    """
    Given a list of Rule data elements, create or update corresponding Rule objects
    or report failure
    """
    logger.info(f"Finding policy with key '{policy_key}'")

    policy = get_policy_or_error(db, policy_key)

    created_or_updated: List[Rule] = []
    failed: List[BulkUpdateFailed] = []

    logger.info(
        f"Starting bulk upsert for {len(input_data)} rules on policy {policy_key}"
    )

    for schema in input_data:
        # Validate all FKs in the input data exist
        associated_storage_config_id = None
        if schema.action_type == ActionType.access:
            # Only validate the associated StorageConfig on access rules
            storage_destination_key = schema.storage_destination_key
            associated_storage_config: StorageConfig = StorageConfig.get_by(
                db=db,
                field="key",
                value=storage_destination_key,
            )
            if not associated_storage_config:
                logger.warning(
                    f"No storage config found with key {storage_destination_key}"
                )
                failure = {
                    "message": f"A StorageConfig with key {storage_destination_key} does not exist",
                    "data": dict(
                        schema
                    ),  # Be sure to pass the schema out the same way it came in
                }
                failed.append(BulkUpdateFailed(**failure))
                continue

            associated_storage_config_id = associated_storage_config.id

        masking_strategy_data = None
        if schema.masking_strategy:
            masking_strategy_data = schema.masking_strategy.dict()

        try:
            rule = Rule.create_or_update(
                db=db,
                data={
                    "action_type": schema.action_type,
                    "client_id": client.id,
                    "key": schema.key,
                    "name": schema.name,
                    "policy_id": policy.id,
                    "storage_destination_id": associated_storage_config_id,
                    "masking_strategy": masking_strategy_data,
                },
            )
        except KeyOrNameAlreadyExists as exc:
            logger.warning(
                f"Create/update failed for rule '{schema.key}' on policy {policy_key}: {exc}"
            )
            failure = {
                "message": exc.args[0],
                "data": dict(schema),
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        except RuleValidationError as exc:
            logger.warning(
                f"Create/update failed for rule '{schema.key}' on policy {policy_key}: {exc}"
            )
            failure = {
                "message": exc.args[0],
                "data": dict(schema),
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        except ValueError as exc:
            logger.warning(
                f"Create/update failed for rule '{schema.key}' on policy {policy_key}: {exc}"
            )
            failure = {
                "message": exc.args[0],
                "data": dict(schema),
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        else:
            created_or_updated.append(rule)

    return schemas.BulkPutRuleResponse(succeeded=created_or_updated, failed=failed)


@router.delete(
    urls.RULE_DETAIL,
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.RULE_DELETE])],
)
def delete_rule(
    *,
    policy_key: FidesOpsKey,
    rule_key: FidesOpsKey,
    db: Session = Depends(deps.get_db),
) -> None:
    """
    Delete a policy rule.
    """
    policy = get_policy_or_error(db, policy_key)

    logger.info(f"Finding rule with key '{rule_key}'")

    rule = Rule.filter(
        db=db, conditions=(Rule.key == rule_key and Rule.policy_id == policy.id)
    ).first()
    if not rule:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Rule found for key {rule_key} on Policy {policy_key}.",
        )

    logger.info(f"Deleting rule with key '{rule_key}'")
    rule.delete(db=db)


@router.patch(
    urls.RULE_TARGET_LIST,
    status_code=HTTP_200_OK,
    response_model=schemas.BulkPutRuleTargetResponse,
)
def create_or_update_rule_targets(
    *,
    client: ClientDetail = Security(
        verify_oauth_client, scopes=[scopes.RULE_CREATE_OR_UPDATE]
    ),
    policy_key: FidesOpsKey,
    rule_key: FidesOpsKey,
    db: Session = Depends(deps.get_db),
    input_data: conlist(schemas.RuleTarget, max_items=50) = Body(...),  # type: ignore
) -> schemas.BulkPutRuleTargetResponse:
    """
    Given a list of Rule data elements, create corresponding Rule objects
    or report failure
    """
    policy = get_policy_or_error(db, policy_key)

    logger.info(f"Finding rule with key '{rule_key}'")
    rule = Rule.filter(
        db=db, conditions=(Rule.key == rule_key and Rule.policy_id == policy.id)
    ).first()
    if not rule:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Rule found for key {rule_key} on Policy {policy_key}.",
        )

    created_or_updated = []
    failed = []
    logger.info(
        f"Starting bulk upsert for {len(input_data)} rule targets on rule {rule_key}"
    )
    for schema in input_data:
        try:
            target = RuleTarget.create_or_update(
                db=db,
                data={
                    "name": schema.name,
                    "key": schema.key,
                    "data_category": schema.data_category,
                    "rule_id": rule.id,
                    "client_id": client.id,
                },
            )
        except KeyOrNameAlreadyExists as exc:
            logger.warning(
                f"Create/update failed for rule target {schema.key} on rule {rule_key}: {exc}"
            )
            failure = {
                "message": exc.args[0],
                "data": dict(schema),
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        except (
            DataCategoryNotSupported,
            PolicyValidationError,
            RuleTargetValidationError,
        ) as exc:
            logger.warning(
                f"Create/update failed for rule target {schema.key} on rule {rule_key}: {exc}"
            )
            failure = {
                "message": exc.args[0],
                "data": dict(schema),
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        except IntegrityError as exc:
            logger.warning(
                f"Create/update failed for rule target {schema.key} on rule {rule_key}: {exc}"
            )
            failure = {
                "message": f"DataCategory {schema.data_category} is already specified on Rule with ID {rule.id}",
                "data": dict(schema),
            }
            failed.append(BulkUpdateFailed(**failure))
        else:
            created_or_updated.append(target)

    return schemas.BulkPutRuleTargetResponse(
        succeeded=created_or_updated,
        failed=failed,
    )


@router.delete(
    urls.RULE_TARGET_DETAIL,
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.RULE_DELETE])],
)
def delete_rule_target(
    *,
    policy_key: FidesOpsKey,
    rule_key: FidesOpsKey,
    rule_target_key: FidesOpsKey,
    db: Session = Depends(deps.get_db),
) -> None:
    """
    Delete the rule target.
    """
    policy = get_policy_or_error(db, policy_key)

    logger.info(f"Finding rule with key '{rule_key}'")
    rule = Rule.filter(
        db=db, conditions=(Rule.key == rule_key and Rule.policy_id == policy.id)
    ).first()
    if not rule:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Rule found for key {rule_key} on Policy {policy_key}.",
        )

    logger.info(f"Finding rule target with key '{rule_target_key}'")
    target = RuleTarget.filter(
        db=db,
        conditions=(
            RuleTarget.key == rule_target_key and RuleTarget.rule_id == rule.id
        ),
    ).first()
    if not target:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No RuleTarget found for key {rule_target_key} at Rule {rule_key} on Policy {policy_key}.",
        )

    logger.info(f"Deleting rule target with key '{rule_target_key}'")

    target.delete(db=db)
