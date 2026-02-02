from typing import Any, Dict, List, Optional, Set

from fastapi import Depends, HTTPException, Request
from fastapi.params import Security
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from fides.api.api import deps
from fides.api.models.application_config import ApplicationConfig
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.application_config import (
    ApplicationConfig as ApplicationConfigSchema,
)
from fides.api.util.api_router import APIRouter
from fides.common.api import scope_registry as scopes
from fides.common.api.v1 import urn_registry as urls
from fides.config import censor_config
from fides.config import get_config as get_app_config
from fides.config.config_proxy import ConfigProxy
from fides.config.validation import ValidationManager

router = APIRouter(tags=["Config"], prefix=urls.V1_URL_PREFIX)


def _extract_setting_paths(data: Dict[str, Any], prefix: str = "") -> Set[str]:
    """
    Extract all setting paths from a nested dictionary.

    Example:
        {"consent": {"tcf_enabled": True}} -> {"consent.tcf_enabled"}
    """
    paths: Set[str] = set()
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            paths.update(_extract_setting_paths(value, path))
        else:
            paths.add(path)
    return paths


def _validate_config_update(
    db: Session,
    changed_settings: Set[str],
) -> List[Dict[str, Any]]:
    """
    Validate proposed config changes against validation rules.

    Returns a list of validation errors (empty if all valid).
    """
    config = get_app_config()
    results = ValidationManager.validate_config_update(config, changed_settings, db)

    errors = ValidationManager.get_errors(results)
    return [
        {
            "rule": e.rule_name,
            "message": e.message,
            "details": e.details,
        }
        for e in errors
    ]


@router.get(
    urls.CONFIG,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.CONFIG_READ])],
    response_model=Dict[str, Any],
)
def get_config(
    *, db: Session = Depends(deps.get_db), api_set: bool = False
) -> Dict[str, Any]:
    """Returns the current API exposable Fides configuration."""
    logger.info("Getting the exposable Fides configuration")
    if api_set:
        logger.info("Retrieving api-set application settings")
        return censor_config(ApplicationConfig.get_api_set(db))
    config = censor_config(get_app_config())
    return config


@router.patch(
    urls.CONFIG,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.CONFIG_UPDATE])],
    response_model=ApplicationConfigSchema,
    response_model_exclude_unset=True,
)
def patch_settings(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    data: ApplicationConfigSchema,
) -> ApplicationConfigSchema:
    """
    Updates the global application settings record.

    Only keys provided will be updated, others will be unaffected,
    i.e. true PATCH behavior.
    """
    # We use exclude_unset=True to ensure that only the provided keys are updated.
    # This is particularly useful for allowing setting a specific key to None, while
    # keeping the existing values for other keys that aren't provided in the payload data.
    pruned_data = data.model_dump(exclude_unset=True)

    # Validate the proposed changes
    changed_settings = _extract_setting_paths(pruned_data)
    validation_errors = _validate_config_update(db, changed_settings)
    if validation_errors:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail={
                "message": "Configuration validation failed",
                "errors": validation_errors,
            },
        )

    logger.info("PATCHing application settings")
    update_config: ApplicationConfig = ApplicationConfig.update_api_set(db, pruned_data)

    ConfigProxy(db).load_current_cors_domains_into_middleware(request.app)

    return update_config.api_set


@router.put(
    urls.CONFIG,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.CONFIG_UPDATE])],
    response_model=ApplicationConfigSchema,
    response_model_exclude_unset=True,
)
def put_settings(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
    data: ApplicationConfigSchema,
) -> ApplicationConfigSchema:
    """
    Updates the global application settings record.

    The record will look exactly as it is provided, i.e. true PUT behavior.
    """
    pruned_data = data.model_dump(exclude_none=True)

    # Validate the proposed changes
    changed_settings = _extract_setting_paths(pruned_data)
    validation_errors = _validate_config_update(db, changed_settings)
    if validation_errors:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail={
                "message": "Configuration validation failed",
                "errors": validation_errors,
            },
        )

    logger.info("PUTing application settings")
    update_config: ApplicationConfig = ApplicationConfig.update_api_set(
        db,
        pruned_data,
        merge_updates=False,
    )

    ConfigProxy(db).load_current_cors_domains_into_middleware(request.app)
    return update_config.api_set


@router.delete(
    urls.CONFIG,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.CONFIG_UPDATE])],
    response_model=Dict,
)
def reset_settings(
    *,
    db: Session = Depends(deps.get_db),
    request: Request,
) -> dict:
    """
    Resets the global application settings record.

    Only the "api-set" values are cleared, "config-set" values are
    not updated via any API calls
    """
    logger.info("Resetting api-set application settings")
    update_config: Optional[ApplicationConfig] = ApplicationConfig.clear_api_set(db)

    ConfigProxy(db).load_current_cors_domains_into_middleware(request.app)

    return update_config.api_set if update_config else {}


@router.get(
    urls.CONFIG + "/validate",
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.CONFIG_READ])],
    response_model=Dict[str, Any],
)
def validate_config(
    *,
    db: Session = Depends(deps.get_db),
) -> Dict[str, Any]:
    """
    Runs all configuration validation rules and returns the results.

    This endpoint can be used to check the current configuration state
    without making any changes. It runs all registered validation rules
    and returns both errors and warnings.

    Returns:
        - valid: True if no ERROR-severity rules failed
        - results: List of all validation results
        - errors: List of ERROR-severity failures (if any)
        - warnings: List of WARNING-severity failures (if any)
    """
    logger.info("Running on-demand configuration validation")
    config = get_app_config()
    results = ValidationManager.validate_all(config, db)

    errors = ValidationManager.get_errors(results)
    warnings = ValidationManager.get_warnings(results)

    return {
        "valid": len(errors) == 0,
        "total_rules": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "errors": [
            {
                "rule": e.rule_name,
                "message": e.message,
                "severity": e.severity.value,
                "details": e.details,
            }
            for e in errors
        ],
        "warnings": [
            {
                "rule": w.rule_name,
                "message": w.message,
                "severity": w.severity.value,
                "details": w.details,
            }
            for w in warnings
        ],
        "results": [
            {
                "rule": r.rule_name,
                "passed": r.passed,
                "message": r.message,
                "severity": r.severity.value,
            }
            for r in results
        ],
    }
