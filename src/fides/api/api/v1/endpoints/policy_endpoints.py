from typing import Annotated, Any, Dict, List, Optional

from fastapi import Depends, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api import deps
from fides.api.common_exceptions import (
    DataCategoryNotSupported,
    DrpActionValidationError,
    KeyOrNameAlreadyExists,
    PolicyValidationError,
    RuleTargetValidationError,
    RuleValidationError,
)
from fides.api.models.client import ClientDetail
from fides.api.models.policy import Policy, Rule, RuleTarget
from fides.api.models.sql_models import DataCategory  # type: ignore
from fides.api.models.storage import StorageConfig
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas import policy as schemas
from fides.api.schemas.api import BulkUpdateFailed
from fides.api.schemas.policy import ActionType
from fides.api.util.api_router import APIRouter
from fides.api.util.logger import Pii
from fides.common.api import scope_registry
from fides.common.api.v1 import urn_registry as urls

router = APIRouter(tags=["DSR Policy"], prefix=urls.V1_URL_PREFIX)


@router.get(
    urls.POLICY_LIST,
    status_code=HTTP_200_OK,
    response_model=Page[schemas.PolicyResponse],
    dependencies=[Security(verify_oauth_client, scopes=[scope_registry.POLICY_READ])],
)
def get_policy_list(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
) -> AbstractPage[Policy]:
    """
    Return a paginated list of all Policy records in this system
    """
    logger.debug("Finding all policies with pagination params '{}'", params)
    policies = Policy.query(db=db).order_by(Policy.created_at.desc())
    return paginate(policies, params=params)


def get_policy_or_error(db: Session, policy_key: FidesKey) -> Policy:
    """Helper method to load Policy or throw a 404"""
    logger.debug("Finding policy with key '{}'", policy_key)
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
    dependencies=[Security(verify_oauth_client, scopes=[scope_registry.POLICY_READ])],
)
def get_policy(
    *,
    policy_key: FidesKey,
    db: Session = Depends(deps.get_db),
) -> schemas.Policy:
    """
    Return a single Policy
    """
    return get_policy_or_error(db, policy_key)  # type: ignore[return-value]


@router.patch(
    urls.POLICY_LIST,
    status_code=HTTP_200_OK,
    response_model=schemas.BulkPutPolicyResponse,
)
def create_or_update_policies(
    *,
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[scope_registry.POLICY_CREATE_OR_UPDATE],
    ),
    db: Session = Depends(deps.get_db),
    data: Annotated[List[schemas.Policy], Field(max_length=50)],  # type: ignore
) -> schemas.BulkPutPolicyResponse:
    """
    Given a list of policy data elements, create or update corresponding Policy objects
    or report failure
    """
    created_or_updated: List[Policy] = []
    failed: List[BulkUpdateFailed] = []
    logger.info("Starting bulk upsert for {} policies", len(data))

    for policy_schema in data:
        policy_data: Dict[str, Any] = dict(policy_schema)
        try:
            policy = Policy.create_or_update(
                db=db,
                data={
                    "name": policy_data["name"],
                    "key": policy_data.get("key"),
                    "drp_action": policy_data.get("drp_action"),
                    "execution_timeframe": policy_data.get("execution_timeframe"),
                },
            )
        except (
            KeyOrNameAlreadyExists,
            DrpActionValidationError,
            IntegrityError,
        ) as exc:
            logger.warning("Create/update failed for policy: {}", Pii(str(exc)))
            failure = {
                "message": exc.args[0],
                "data": policy_data,
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        except PolicyValidationError as exc:
            logger.warning("Create/update failed for policy: {}", Pii(str(exc)))
            failure = {
                "message": "This record could not be added because the data provided was invalid.",
                "data": policy_data,
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        else:
            created_or_updated.append(policy)  # type: ignore[arg-type]

    return schemas.BulkPutPolicyResponse(
        succeeded=created_or_updated,
        failed=failed,
    )


def get_rule_or_error(db: Session, policy_key: FidesKey, rule_key: FidesKey) -> Rule:
    """
    Helper method to load Rule or throw a 404 if it can't be found.
    Also throws a 404 if a `Policy` with the given key can't be found.
    """
    policy = get_policy_or_error(db, policy_key)
    logger.debug("Finding rule with key '{}'", rule_key)
    rule = Rule.filter(
        db=db,
        conditions=((Rule.policy_id == policy.id) & (Rule.key == rule_key)),
    ).first()
    if not rule:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Rule found for key {rule_key} attached to policy {policy_key}",
        )

    return rule


@router.get(
    urls.RULE_LIST,
    status_code=HTTP_200_OK,
    response_model=Page[schemas.RuleResponseWithTargets],
    dependencies=[Security(verify_oauth_client, scopes=[scope_registry.RULE_READ])],
)
def get_rule_list(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    params: Params = Depends(),
) -> AbstractPage[Rule]:
    """
    Return a paginated list of all `Rule` records associated with the given `Policy`.
    Throws a 404 if the given `Policy` can't be found.
    """
    policy = get_policy_or_error(db, policy_key)
    logger.debug(
        "Finding all rules for policy {} with pagination params '{}'",
        policy_key,
        params,
    )
    rules = Rule.filter(
        db=db,
        conditions=(Rule.policy_id == policy.id),
    ).order_by(Rule.created_at.desc())
    return paginate(rules, params=params)


@router.get(
    urls.RULE_DETAIL,
    status_code=HTTP_200_OK,
    response_model=schemas.RuleResponseWithTargets,
    dependencies=[Security(verify_oauth_client, scopes=[scope_registry.RULE_READ])],
)
def get_rule(
    *,
    policy_key: FidesKey,
    rule_key: FidesKey,
    db: Session = Depends(deps.get_db),
) -> Rule:
    """
    Return a single `Rule` with the given key, associated with the given `Policy`
    """
    return get_rule_or_error(db, policy_key, rule_key)


@router.patch(
    urls.RULE_LIST,
    status_code=HTTP_200_OK,
    response_model=schemas.BulkPutRuleResponse,
)
def create_or_update_rules(
    *,
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[scope_registry.RULE_CREATE_OR_UPDATE],
    ),
    policy_key: FidesKey,
    db: Session = Depends(deps.get_db),
    input_data: Annotated[List[schemas.RuleCreate], Field(max_length=50)],  # type: ignore
) -> schemas.BulkPutRuleResponse:
    """
    Given a list of Rule data elements, create or update corresponding Rule objects
    or report failure
    """
    logger.info("Finding policy with key '{}'", policy_key)

    policy = get_policy_or_error(db, policy_key)

    created_or_updated: List[Rule] = []
    failed: List[BulkUpdateFailed] = []

    logger.info(
        "Starting bulk upsert for {} rules on policy {}", len(input_data), policy_key
    )

    for schema in input_data:
        # Validate all FKs in the input data exist
        associated_storage_config_id = None
        if schema.action_type == ActionType.access:
            # Only validate the associated StorageConfig on access rules
            storage_destination_key = schema.storage_destination_key
            # storage key doesn't need to be specified, as there is a default to fallback to
            if storage_destination_key:
                associated_storage_config: Optional[StorageConfig] = (
                    StorageConfig.get_by(
                        db=db,
                        field="key",
                        value=storage_destination_key,
                    )
                )
                if not associated_storage_config:
                    logger.warning(
                        "No storage config found with key {}", storage_destination_key
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
            masking_strategy_data = schema.masking_strategy.model_dump(mode="json")

        try:
            rule = Rule.create_or_update(
                db=db,
                data={
                    "action_type": schema.action_type,
                    "key": schema.key,
                    "name": schema.name,
                    "policy_id": policy.id,
                    "storage_destination_id": associated_storage_config_id,
                    "masking_strategy": masking_strategy_data,
                },
            )
        except KeyOrNameAlreadyExists as exc:
            logger.warning(
                "Create/update failed for rule '{}' on policy {}: {}",
                schema.key,
                policy_key,
                exc,
            )
            failure = {
                "message": exc.args[0],
                "data": dict(schema),
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        except RuleValidationError as exc:
            logger.warning(
                "Create/update failed for rule '{}' on policy {}: {}",
                schema.key,
                policy_key,
                Pii(str(exc)),
            )
            failure = {
                "message": exc.args[0],
                "data": dict(schema),
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        except ValueError as exc:
            logger.warning(
                "Create/update failed for rule '{}' on policy {}: {}",
                schema.key,
                policy_key,
                Pii(str(exc)),
            )
            failure = {
                "message": exc.args[0],
                "data": dict(schema),
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        else:
            created_or_updated.append(rule)  # type: ignore[arg-type]

    return schemas.BulkPutRuleResponse(succeeded=created_or_updated, failed=failed)


@router.delete(
    urls.RULE_DETAIL,
    status_code=HTTP_204_NO_CONTENT,
    dependencies=[Security(verify_oauth_client, scopes=[scope_registry.RULE_DELETE])],
)
def delete_rule(
    *,
    policy_key: FidesKey,
    rule_key: FidesKey,
    db: Session = Depends(deps.get_db),
) -> None:
    """
    Delete a policy rule.
    """
    policy = get_policy_or_error(db, policy_key)

    logger.info("Finding rule with key '{}'", rule_key)

    rule = Rule.filter(
        db=db, conditions=(Rule.key == rule_key and Rule.policy_id == policy.id)  # type: ignore[arg-type]
    ).first()
    if not rule:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Rule found for key {rule_key} on Policy {policy_key}.",
        )

    logger.info("Deleting rule with key '{}'", rule_key)
    rule.delete(db=db)


def get_rule_target_or_error(
    db: Session,
    policy_key: FidesKey,
    rule_key: FidesKey,
    rule_target_key: FidesKey,
) -> RuleTarget:
    """
    Helper method to load Rule Target or throw a 404.
    Also throws a 404 if a `Policy` or `Rule` with the given keys can't be found.
    """
    logger.debug("Finding rule target with key '{}'", rule_target_key)
    rule: Rule = get_rule_or_error(db, policy_key, rule_key)
    rule_target = RuleTarget.filter(
        db=db,
        conditions=(
            (RuleTarget.rule_id == rule.id) & (RuleTarget.key == rule_target_key)
        ),
    ).first()
    if not rule_target:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Rule Target found for key {rule_target_key} attached to rule {rule_key}.",
        )

    return rule_target


@router.get(
    urls.RULE_TARGET_LIST,
    status_code=HTTP_200_OK,
    response_model=Page[schemas.RuleTarget],
    dependencies=[Security(verify_oauth_client, scopes=[scope_registry.RULE_READ])],
)
def get_rule_target_list(
    *,
    db: Session = Depends(deps.get_db),
    policy_key: FidesKey,
    rule_key: FidesKey,
    params: Params = Depends(),
) -> AbstractPage[RuleTarget]:
    """
    Return a paginated list of all `Rule Target` records associated with the given `Rule`
    Throws a 404 if the given `Rule` or `Policy` can't be found.
    """
    rule = get_rule_or_error(db, policy_key, rule_key)
    logger.debug(
        "Finding all rule targets for rule {} with pagination params '{}'",
        rule_key,
        params,
    )
    rule_targets = RuleTarget.filter(
        db=db,
        conditions=(RuleTarget.rule_id == rule.id),
    ).order_by(RuleTarget.created_at.desc())
    return paginate(rule_targets, params=params)


@router.get(
    urls.RULE_TARGET_DETAIL,
    status_code=HTTP_200_OK,
    response_model=schemas.RuleTarget,
    dependencies=[Security(verify_oauth_client, scopes=[scope_registry.RULE_READ])],
)
def get_rule_target(
    *,
    policy_key: FidesKey,
    rule_key: FidesKey,
    rule_target_key: FidesKey,
    db: Session = Depends(deps.get_db),
) -> RuleTarget:
    """
    Return a single `Rule Target` associated with the given `Rule` and `Policy`
    """
    return get_rule_target_or_error(db, policy_key, rule_key, rule_target_key)


def _validate_data_categories(
    db: Session,
    data_categories: List[str],
) -> None:
    """
    Helper method to validate that all data categories supplied to the endpoint
    exist in the database
    """
    from_db = [
        dc.fides_key
        for dc in DataCategory.filter(
            db=db,
            conditions=DataCategory.fides_key.in_(data_categories),
        ).all()
    ]
    invalid_categories = list(set(data_categories) - set(from_db))
    if invalid_categories:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid data categories: {invalid_categories}",
        )


@router.patch(
    urls.RULE_TARGET_LIST,
    status_code=HTTP_200_OK,
    response_model=schemas.BulkPutRuleTargetResponse,
)
def create_or_update_rule_targets(
    *,
    client: ClientDetail = Security(
        verify_oauth_client, scopes=[scope_registry.RULE_CREATE_OR_UPDATE]
    ),
    policy_key: FidesKey,
    rule_key: FidesKey,
    db: Session = Depends(deps.get_db),
    input_data: Annotated[List[schemas.RuleTarget], Field(max_length=50)],  # type: ignore
) -> schemas.BulkPutRuleTargetResponse:
    """
    Given a list of Rule data elements, create corresponding Rule objects
    or report failure
    """
    policy = get_policy_or_error(db, policy_key)

    logger.info("Finding rule with key '{}'", rule_key)
    rule = Rule.filter(
        db=db, conditions=(Rule.key == rule_key and Rule.policy_id == policy.id)  # type: ignore[arg-type]
    ).first()
    if not rule:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Rule found for key {rule_key} on Policy {policy_key}.",
        )

    _validate_data_categories(
        db=db,
        data_categories=[schema.data_category for schema in input_data],
    )

    created_or_updated = []
    failed = []
    logger.info(
        "Starting bulk upsert for {} rule targets on rule {}", len(input_data), rule_key
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
                },
            )
        except KeyOrNameAlreadyExists as exc:
            logger.warning(
                "Create/update failed for rule target {} on rule {}: {}",
                schema.key,
                rule_key,
                exc,
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
                "Create/update failed for rule target {} on rule {}: {}",
                schema.key,
                rule_key,
                Pii(str(exc)),
            )
            failure = {
                "message": exc.args[0],
                "data": dict(schema),
            }
            failed.append(BulkUpdateFailed(**failure))
            continue
        except IntegrityError as exc:
            logger.warning(
                "Create/update failed for rule target {} on rule {}: {}",
                schema.key,
                rule_key,
                Pii(str(exc)),
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
    dependencies=[Security(verify_oauth_client, scopes=[scope_registry.RULE_DELETE])],
)
def delete_rule_target(
    *,
    policy_key: FidesKey,
    rule_key: FidesKey,
    rule_target_key: FidesKey,
    db: Session = Depends(deps.get_db),
) -> None:
    """
    Delete the rule target.
    """
    policy = get_policy_or_error(db, policy_key)

    logger.info("Finding rule with key '{}'", rule_key)
    rule = Rule.filter(
        db=db, conditions=(Rule.key == rule_key and Rule.policy_id == policy.id)  # type: ignore[arg-type]
    ).first()
    if not rule:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Rule found for key {rule_key} on Policy {policy_key}.",
        )

    logger.info("Finding rule target with key '{}'", rule_target_key)
    target = RuleTarget.filter(
        db=db,
        conditions=(
            RuleTarget.key == rule_target_key and RuleTarget.rule_id == rule.id  # type: ignore[arg-type]
        ),
    ).first()
    if not target:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No RuleTarget found for key {rule_target_key} at Rule {rule_key} on Policy {policy_key}.",
        )

    logger.info("Deleting rule target with key '{}'", rule_target_key)

    target.delete(db=db)
