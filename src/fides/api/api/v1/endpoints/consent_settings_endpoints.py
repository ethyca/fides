from fastapi import Depends
from fastapi.params import Security
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.api import deps
from fides.api.models.consent_settings import ConsentSettings
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.consent_settings import (
    ConsentSettingsRequestSchema,
    ConsentSettingsResponseSchema,
)
from fides.api.util.api_router import APIRouter
from fides.common.api import scope_registry as scopes
from fides.common.api.v1 import urn_registry as urls

router = APIRouter(tags=["Consent Settings"], prefix=urls.V1_URL_PREFIX)


@router.get(
    urls.CONSENT_SETTINGS,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.CONSENT_SETTINGS_READ])],
    response_model=ConsentSettingsResponseSchema,
)
def get_consent_settings(*, db: Session = Depends(deps.get_db)) -> ConsentSettings:
    """Endpoint that returns organization-wide consent settings."""
    logger.info("Getting organization-wide consent settings")
    return ConsentSettings.get_or_create_with_defaults(db)


@router.patch(
    urls.CONSENT_SETTINGS,
    dependencies=[
        Security(verify_oauth_client, scopes=[scopes.CONSENT_SETTINGS_UPDATE])
    ],
    response_model=ConsentSettingsResponseSchema,
)
def patch_consent_settings(
    *, db: Session = Depends(deps.get_db), data: ConsentSettingsRequestSchema
) -> ConsentSettings:
    """Update organization-wide consent settings. Only the single record is updated."""
    logger.info("Updating organization-wide consent settings")
    consent_settings_record = ConsentSettings.get_or_create_with_defaults(db)
    return consent_settings_record.update(db=db, data=data.dict())  # type: ignore[return-value]
