from typing import Any, Dict, Optional

from fastapi import Depends
from fastapi.params import Security
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

from fides.api.ops.api import deps
from fides.api.ops.api.v1 import scope_registry as scopes
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.models.application_config import ApplicationConfig
from fides.api.ops.schemas.application_config import (
    ApplicationConfig as ApplicationConfigSchema,
)
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.core.config import censor_config
from fides.core.config import get_config as get_app_config

router = APIRouter(tags=["Config"], prefix=urls.V1_URL_PREFIX)


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
def update_settings(
    *,
    db: Session = Depends(deps.get_db),
    data: ApplicationConfigSchema,
) -> ApplicationConfigSchema:
    """
    Updates the global application settings record.

    Only keys provided will be updated, others will be unaffected,
    i.e. true PATCH behavior.
    """
    logger.info("Updating application settings")
    update_config: ApplicationConfig = ApplicationConfig.update_api_set(
        db, data.dict(exclude_none=True)
    )
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
) -> dict:
    """
    Resets the global application settings record.

    Only the "api-set" values are cleared, "config-set" values are
    not updated via any API calls
    """
    logger.info("Resetting api-set application settings")
    update_config: Optional[ApplicationConfig] = ApplicationConfig.clear_api_set(db)
    return update_config.api_set if update_config else {}
