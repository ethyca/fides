from typing import List, Optional

from fastapi import Depends, HTTPException, Request, Security
from fastapi_pagination import Page, Params
from fastapi_pagination import paginate as fastapi_paginate
from fastapi_pagination.bases import AbstractPage
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.ops.api import deps
from fides.api.ops.api.v1 import scope_registry
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.api.v1.endpoints.privacy_preference_endpoints import verify_address
from fides.api.ops.models.privacy_experience import ComponentType, PrivacyExperience
from fides.api.ops.models.privacy_notice import PrivacyNotice, PrivacyNoticeRegion
from fides.api.ops.models.privacy_request import ProvidedIdentity
from fides.api.ops.oauth.utils import verify_oauth_client
from fides.api.ops.schemas.privacy_experience import PrivacyExperienceResponse
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.consent_util import get_fides_user_device_id_provided_identity

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
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_EXPERIENCE_READ])
    ],
)
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
    request: Request,
) -> AbstractPage[PrivacyExperience]:
    """
    Returns a list of PrivacyExperience records for individual regions with
    relevant privacy notices embedded in the response.

    'show_disabled' query params are passed along to further filter
    notices as well.
    """
    logger.info("Finding all Privacy Experiences with pagination params '{}'", params)
    fides_user_provided_identity: Optional[ProvidedIdentity] = None
    if fides_user_device_id:
        verify_address(request)
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


@router.get(
    urls.PRIVACY_EXPERIENCE_DETAIL,
    status_code=HTTP_200_OK,
    response_model=PrivacyExperienceResponse,
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_EXPERIENCE_READ])
    ],
)
def privacy_experience_detail(
    *,
    db: Session = Depends(deps.get_db),
    privacy_experience_id: str,
    show_disabled: Optional[bool] = True,
) -> PrivacyExperience:
    """
    Return a privacy experience for a given region with relevant notices embedded.

    show_disabled query params are passed onto optionally filter the embedded notices.
    """
    logger.info("Fetching privacy experience with id '{}'.", privacy_experience_id)
    experience: PrivacyExperience = get_privacy_experience_or_error(
        db, privacy_experience_id
    )

    if show_disabled is False and experience.disabled:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Query param show_disabled=False not applicable for disabled privacy experience {privacy_experience_id}.",
        )

    # Temporarily stash the privacy notices on the experience for display
    experience.privacy_notices = experience.get_related_privacy_notices(
        db, show_disabled
    )
    return experience
