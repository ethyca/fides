from typing import List, Optional

from fastapi import Depends, HTTPException, Security
from fastapi_pagination import Page, Params
from fastapi_pagination import paginate as fastapi_paginate
from fastapi_pagination.bases import AbstractPage
from loguru import logger
from pydantic import conlist
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.ops.api import deps
from fides.api.ops.api.v1 import scope_registry
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.models.privacy_experience import ComponentType, PrivacyExperience
from fides.api.ops.models.privacy_notice import PrivacyNotice, PrivacyNoticeRegion
from fides.api.ops.schemas.privacy_experience import (
    PrivacyExperienceCreate,
    PrivacyExperienceResponse,
    PrivacyExperienceWithId,
)
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.oauth_util import verify_oauth_client

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
) -> AbstractPage[PrivacyExperience]:
    """
    Return a paginated list of `PrivacyExperience` records in this system.
    Includes some query params to help filter the list if needed. Returns
    relevant privacy notices embedded in the experience response.

    'region' and 'show_disabled' query params are passed along to further filter
    notices as well.
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


@router.post(
    urls.PRIVACY_EXPERIENCE,
    status_code=HTTP_201_CREATED,
    response_model=List[PrivacyExperienceResponse],
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_EXPERIENCE_CREATE])
    ],
)
def privacy_experience_create(
    *,
    db: Session = Depends(deps.get_db),
    bulk_experience_data: conlist(PrivacyExperienceCreate, max_items=50),  # type: ignore
) -> List[PrivacyExperience]:
    """
    Bulk create Privacy Experiences. Returns related notices in the response.
    """
    logger.info("Creating privacy experiences")
    experiences: List[PrivacyExperience] = []
    for experience_data in bulk_experience_data:
        experience = PrivacyExperience.create(
            db, data=experience_data.dict(exclude_unset=True), check_name=False
        )
        # Temporarily stash the privacy notices on the experience for display
        experience.privacy_notices = experience.get_related_privacy_notices(db)
        experiences.append(experience)
    return experiences


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
    region: Optional[PrivacyNoticeRegion] = None,
) -> PrivacyExperience:
    """
    Get privacy experience with embedded notices.

    show_disabled and region_query params are passed onto optionally filter the embedded notices.
    """
    logger.info("Fetching privacy experience with it {}", privacy_experience_id)
    experience: PrivacyExperience = get_privacy_experience_or_error(
        db, privacy_experience_id
    )
    if region and region not in experience.regions:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Region query param {region.value} not applicable for privacy experience {privacy_experience_id}.",
        )

    if show_disabled is False and experience.disabled:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Query param show_disabled=False not applicable for disabled privacy experience {privacy_experience_id}.",
        )

    # Temporarily stash the privacy notices on the experience for display
    experience.privacy_notices = experience.get_related_privacy_notices(
        db, region, show_disabled
    )
    return experience


def ensure_unique_ids(
    privacy_experience_updates: List[PrivacyExperienceWithId],
) -> None:
    """Verifies privacy experience ids are unique in request to avoid unexpected behavior"""
    request_ids: List[str] = [update.id for update in privacy_experience_updates]
    if len(request_ids) != len(set(request_ids)):
        raise HTTPException(
            HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Duplicate privacy experience ids submitted in request.",
        )


@router.patch(
    urls.PRIVACY_EXPERIENCE,
    status_code=HTTP_200_OK,
    response_model=List[PrivacyExperienceResponse],
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_EXPERIENCE_UPDATE])
    ],
)
def privacy_experience_bulk_update(
    *,
    db: Session = Depends(deps.get_db),
    privacy_experience_updates: conlist(PrivacyExperienceWithId, max_items=50),  # type: ignore
) -> List[PrivacyExperience]:
    """
    Bulk update privacy experiences.  Related notices are returned in the response.
    """
    ensure_unique_ids(privacy_experience_updates)

    loaded_privacy_experiences: List[PrivacyExperience] = [
        get_privacy_experience_or_error(db, experience_update.id)
        for experience_update in privacy_experience_updates
    ]

    return [
        existing_experience.update(
            db, data=experience_update_data.dict(exclude_unset=True)
        )
        for (existing_experience, experience_update_data) in zip(
            loaded_privacy_experiences, privacy_experience_updates
        )
    ]
