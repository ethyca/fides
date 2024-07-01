from typing import Any, Dict, Optional

from fastapi import Depends, Request
from fastapi.params import Security
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

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

    pruned_data = data.model_dump(exclude_none=True)
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
