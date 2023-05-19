from typing import List, Optional

from fastapi import Depends, HTTPException, Request, Response
from fastapi_pagination import Page, Params
from fastapi_pagination import paginate as fastapi_paginate
from fastapi_pagination.bases import AbstractPage
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from fides.api.api import deps
from fides.api.api.v1 import urn_registry as urls
from fides.api.api.v1.endpoints.utils import fides_limiter
from fides.api.models.privacy_experience import ComponentType, PrivacyExperience
from fides.api.models.privacy_notice import PrivacyNotice, PrivacyNoticeRegion
from fides.api.models.privacy_request import ProvidedIdentity
from fides.api.schemas.privacy_experience import PrivacyExperienceResponse
from fides.api.util.api_router import APIRouter
from fides.api.util.consent_util import get_fides_user_device_id_provided_identity
from fides.core.config import CONFIG

router = APIRouter(tags=["Privacy Experience"], prefix=urls.V1_URL_PREFIX)


def get_privacy_experience_or_error(
    db: Session, experience_id: str
) -> PrivacyExperience:
    """
    Helper method to load PrivacyExperience or throw a 404
    """
    logger.info("Finding PrivacyExperience with id '{}'", experience_id)
    privacy_experience = PrivacyExperience.get(db=db, object_id=experience_id)
    if not privacy_experience:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No PrivacyExperience found for id {experience_id}.",
        )

    return privacy_experience


@router.get(
    urls.PRIVACY_EXPERIENCE,
    status_code=HTTP_200_OK,
    response_model=Page[PrivacyExperienceResponse],
)
@fides_limiter.limit(CONFIG.security.public_request_rate_limit)
def privacy_experience_list(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    show_disabled: Optional[bool] = True,
    region: Optional[PrivacyNoticeRegion] = None,
    component: Optional[ComponentType] = None,
    has_notices: Optional[bool] = None,
    has_config: Optional[bool] = None,
    fides_user_device_id: Optional[str] = None,
    request: Request,  # required for rate limiting
    response: Response,  # required for rate limiting
) -> AbstractPage[PrivacyExperience]:
    """
    Public endpoint that returns a list of PrivacyExperience records for individual regions with
    relevant privacy notices embedded in the response.

    'show_disabled' query params are passed along to further filter
    notices as well.

    'fides_user_device_id' query param will stash the current preferences of the given user
    alongside each notice where applicable.
    """
    logger.info("Finding all Privacy Experiences with pagination params '{}'", params)
    fides_user_provided_identity: Optional[ProvidedIdentity] = None
    if fides_user_device_id:
        fides_user_provided_identity = get_fides_user_device_id_provided_identity(
            db=db, fides_user_device_id=fides_user_device_id
        )

    experience_query = db.query(PrivacyExperience)

    if show_disabled is False:
        experience_query = experience_query.filter(
            PrivacyExperience.disabled.is_(False)
        )
    if region is not None:
        experience_query = experience_query.filter(PrivacyExperience.region == region)
    if component is not None:
        experience_query = experience_query.filter(
            PrivacyExperience.component == component
        )
    if has_config is True:
        experience_query = experience_query.filter(
            PrivacyExperience.experience_config_id.isnot(None)
        )
    if has_config is False:
        experience_query = experience_query.filter(
            PrivacyExperience.experience_config_id.is_(None)
        )

    results: List[PrivacyExperience] = []
    for privacy_experience in experience_query.order_by(
        PrivacyExperience.created_at.desc()
    ):
        privacy_notices: List[
            PrivacyNotice
        ] = privacy_experience.get_related_privacy_notices(
            db, show_disabled, fides_user_provided_identity
        )
        privacy_experience.privacy_notices = privacy_notices
        if not (has_notices and not privacy_notices):
            results.append(privacy_experience)

    return fastapi_paginate(results, params=params)
