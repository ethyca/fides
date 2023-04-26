from typing import List, Optional

from fastapi import Depends, Security
from fastapi_pagination import Page, Params
from fastapi_pagination import paginate as fastapi_paginate
from fastapi_pagination.bases import AbstractPage
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

from fides.api.ops.api import deps
from fides.api.ops.api.v1 import scope_registry
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.models.privacy_experience import ComponentType, PrivacyExperience
from fides.api.ops.models.privacy_notice import PrivacyNotice, PrivacyNoticeRegion
from fides.api.ops.schemas.privacy_experience import PrivacyExperienceResponse
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["Privacy Experience"], prefix=urls.V1_URL_PREFIX)


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
) -> AbstractPage[PrivacyExperience]:
    """
    Return a paginated list of `PrivacyExperience` records in this system.
    Includes some query params to help filter the list if needed
    """
    logger.info("Finding all Privacy Experiences with pagination params '{}'", params)
    experience_query = db.query(PrivacyExperience)

    if show_disabled is False:
        experience_query = experience_query.filter(
            PrivacyExperience.disabled.is_(False)
        )
    if region is not None:
        experience_query = experience_query.filter(
            PrivacyExperience.regions.contains([region])
        )
    if component is not None:
        experience_query = experience_query.filter(
            PrivacyExperience.component == component
        )

    results: List[PrivacyExperience] = []
    for privacy_experience in experience_query.order_by(
        PrivacyExperience.created_at.desc()
    ):
        privacy_notices: List[
            PrivacyNotice
        ] = privacy_experience.get_related_privacy_notices(db, region, show_disabled)
        privacy_experience.privacy_notices = privacy_notices
        if not (has_notices and not privacy_notices):
            results.append(privacy_experience)

    return fastapi_paginate(results, params=params)
