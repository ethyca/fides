from typing import Any, Dict

from fastapi import Depends, Security
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

from fides.api.ops.api import deps
from fides.api.ops.api.v1.scope_registry import SETTINGS_READ, SETTINGS_UPDATE
from fides.api.ops.api.v1.urn_registry import APPLICATION_SETTINGS, V1_URL_PREFIX
from fides.api.ops.models.application_settings import ApplicationSettings
from fides.api.ops.schemas.application_settings import (
    ApplicationSettings as ApplicationSettingsSchema,
)
from fides.api.ops.schemas.application_settings import (
    ApplicationSettingsUpdate as ApplicationSettingsUpdateSchema,
)
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["Application Settings"], prefix=V1_URL_PREFIX)


@router.patch(
    APPLICATION_SETTINGS,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[SETTINGS_UPDATE])],
    response_model=ApplicationSettingsSchema,
)
def update_settings(
    *,
    db: Session = Depends(deps.get_db),
    data: ApplicationSettingsUpdateSchema,
) -> ApplicationSettingsSchema:
    """
    Updates the global application settings record.

    Only keys provided will be updated, others will be unaffected,
    i.e. true PATCH behavior.
    """
    logger.info("Updating application settings")

    updated_settings: ApplicationSettings = ApplicationSettings.create_or_update(
        db, data={"api_set": data.dict()}
    )
    return updated_settings.api_set


@router.get(
    APPLICATION_SETTINGS,
    dependencies=[Security(verify_oauth_client, scopes=[SETTINGS_READ])],
    response_model=ApplicationSettingsSchema,
)
def read_settings(*, db: Session = Depends(deps.get_db)) -> Dict[str, Any]:
    """
    Retrieves the application settings that have been set through the API
    """
    logger.info("Retrieving api-set application settings")
    return ApplicationSettings.get_api_set_settings(db)
