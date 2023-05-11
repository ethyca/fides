from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, Security
from fastapi_pagination import Page, Params
from fastapi_pagination import paginate as fastapi_paginate
from fastapi_pagination.bases import AbstractPage
from loguru import logger
from sqlalchemy.orm import Query, Session
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
from fides.api.ops.api.v1.scope_registry import PRIVACY_EXPERIENCE_UPDATE
from fides.api.ops.models.privacy_experience import (
    ComponentType,
    PrivacyExperience,
    PrivacyExperienceConfig,
    upsert_privacy_experiences_after_config_update,
)
from fides.api.ops.models.privacy_notice import PrivacyNotice, PrivacyNoticeRegion
from fides.api.ops.oauth.utils import verify_oauth_client
from fides.api.ops.schemas.privacy_experience import (
    ExperienceConfigCreate,
    ExperienceConfigCreateOrUpdateResponse,
    ExperienceConfigResponse,
    ExperienceConfigUpdate,
    PrivacyExperienceResponse,
)
from fides.api.ops.util.api_router import APIRouter

router = APIRouter(tags=["Privacy Experience"], prefix=urls.V1_URL_PREFIX)


def get_experience_config_or_error(
    db: Session, experience_config_id: str
) -> PrivacyExperienceConfig:
    """
    Helper method to load ExperienceConfig or throw a 404
    """
    logger.info("Finding PrivacyExperienceConfig with id '{}'", experience_config_id)
    experience_config = PrivacyExperienceConfig.get(
        db=db, object_id=experience_config_id
    )
    if not experience_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No PrivacyExperienceConfig found for id '{experience_config_id}'.",
        )

    return experience_config


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
    Returns a list of PrivacyExperience records for individual regions with
    relevant privacy notices embedded in the response.

    'show_disabled' query params are passed along to further filter
    notices as well.
    """
    logger.info("Finding all Privacy Experiences with pagination params '{}'", params)
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

    results: List[PrivacyExperience] = []
    for privacy_experience in experience_query.order_by(
        PrivacyExperience.created_at.desc()
    ):
        privacy_notices: List[
            PrivacyNotice
        ] = privacy_experience.get_related_privacy_notices(db, show_disabled)
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
    logger.info("Fetching privacy experience with id {}", privacy_experience_id)
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


def remove_config_from_matched_experiences(
    db: Session,
    experience_config: PrivacyExperienceConfig,
    regions_to_unlink: List[PrivacyNoticeRegion],
) -> List[PrivacyExperience]:
    """Remove the config from linked PrivacyExperiences"""
    experiences_to_unlink: List[PrivacyExperience] = experience_config.experiences.filter(  # type: ignore[call-arg]
        PrivacyExperience.region.in_(regions_to_unlink)
    ).all()
    for experience in experiences_to_unlink:
        experience.unlink_privacy_experience_config(db)
    return experiences_to_unlink


@router.get(
    urls.EXPERIENCE_CONFIG,
    status_code=HTTP_200_OK,
    response_model=Page[ExperienceConfigResponse],
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_EXPERIENCE_READ])
    ],
)
def experience_config_list(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    show_disabled: Optional[bool] = True,
    component: Optional[ComponentType] = None,
    region: Optional[PrivacyNoticeRegion] = None,
) -> AbstractPage[PrivacyExperienceConfig]:
    """
    Returns a list of PrivacyExperienceConfig resources.  These resources have common titles, descriptions, and
    labels that can be shared between multiple experiences.
    """

    privacy_experience_config_query: Query = db.query(PrivacyExperienceConfig)

    if component:
        privacy_experience_config_query = privacy_experience_config_query.filter(
            PrivacyExperienceConfig.component == component
        )

    if show_disabled is False:
        privacy_experience_config_query = privacy_experience_config_query.filter(
            PrivacyExperienceConfig.disabled.is_(False)
        )

    if region:
        privacy_experience_config_query = privacy_experience_config_query.join(
            PrivacyExperience,
            PrivacyExperienceConfig.id == PrivacyExperience.experience_config_id,
        ).filter(PrivacyExperience.region == region)

    privacy_experience_config_query = privacy_experience_config_query.order_by(
        PrivacyExperienceConfig.created_at.desc()
    )

    return fastapi_paginate(privacy_experience_config_query.all(), params=params)


@router.post(
    urls.EXPERIENCE_CONFIG,
    status_code=HTTP_201_CREATED,
    response_model=ExperienceConfigCreateOrUpdateResponse,
    dependencies=[
        Security(
            verify_oauth_client,
            scopes=[
                scope_registry.PRIVACY_EXPERIENCE_CREATE,
                PRIVACY_EXPERIENCE_UPDATE,
            ],
        )
    ],
)
def experience_config_create(
    *,
    db: Session = Depends(deps.get_db),
    experience_config_data: ExperienceConfigCreate,
) -> ExperienceConfigCreateOrUpdateResponse:
    """
    Create Experience Language and then attempt to upsert Experiences and link to ExperienceConfig
    """
    logger.info(
        "Creating experience config of component {} and delivery mechanism {} for regions {}.",
        experience_config_data.component,
        experience_config_data.delivery_mechanism,
        experience_config_data.regions,
    )
    experience_config_dict: Dict = experience_config_data.dict(exclude_unset=True)
    new_regions: List[PrivacyNoticeRegion] = experience_config_dict.pop("regions")

    experience_config = PrivacyExperienceConfig.create(
        db, data=experience_config_dict, check_name=False
    )

    added, removed, skipped = upsert_privacy_experiences_after_config_update(
        db, experience_config, new_regions
    )

    return ExperienceConfigCreateOrUpdateResponse(
        experience_config=experience_config,
        added_regions=added,
        removed_regions=removed,
        skipped_regions=skipped,
    )


@router.get(
    urls.EXPERIENCE_CONFIG_DETAIL,
    status_code=HTTP_200_OK,
    response_model=ExperienceConfigResponse,
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_EXPERIENCE_READ])
    ],
)
def experience_config_detail(
    *,
    db: Session = Depends(deps.get_db),
    experience_config_id: str,
) -> PrivacyExperienceConfig:
    """
    Returns a PrivacyExperienceConfig.
    """

    return get_experience_config_or_error(db, experience_config_id)


@router.patch(
    urls.EXPERIENCE_CONFIG_DETAIL,
    status_code=HTTP_200_OK,
    response_model=ExperienceConfigCreateOrUpdateResponse,
    dependencies=[
        Security(
            verify_oauth_client,
            scopes=[
                PRIVACY_EXPERIENCE_UPDATE,
            ],
        )
    ],
)
def experience_config_update(
    *,
    db: Session = Depends(deps.get_db),
    experience_config_id: str,
    experience_config_data: ExperienceConfigUpdate,
) -> ExperienceConfigCreateOrUpdateResponse:
    """
    Update Experience Config and then attempt to upsert Experiences and link back to ExperienceConfig
    """
    experience_config: PrivacyExperienceConfig = get_experience_config_or_error(
        db, experience_config_id
    )
    experience_config_data_dict: Dict = experience_config_data.dict(exclude_unset=True)
    regions: List[PrivacyNoticeRegion] = experience_config_data_dict.pop("regions")

    # Because we're allowing patch updates here, first do a dry update and make sure the experience
    # config wouldn't be put in a bad state.
    dry_update: PrivacyExperienceConfig = experience_config.dry_update(
        data=experience_config_data_dict
    )
    try:
        ExperienceConfigCreate.from_orm(dry_update)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            # pylint: disable=no-member
            detail=exc.errors(),  # type: ignore
        )

    logger.info("Updating experience config of id '{}'", experience_config.id)
    experience_config.update(db=db, data=experience_config_data_dict)

    # Upserting PrivacyExperiences based on regions specified in the request
    current_regions: List[PrivacyNoticeRegion] = experience_config.regions
    not_included_in_request: List[
        PrivacyExperience
    ] = remove_config_from_matched_experiences(
        db,
        experience_config,
        [
            PrivacyNoticeRegion(reg)
            for reg in {reg.value for reg in current_regions}.difference(
                {reg.value for reg in regions}
            )
        ],
    )

    (
        added,
        removed_for_conflict,
        skipped,
    ) = upsert_privacy_experiences_after_config_update(db, experience_config, regions)
    return ExperienceConfigCreateOrUpdateResponse(
        experience_config=experience_config,
        added_regions=added,
        removed_regions=removed_for_conflict
        + [omitted.region for omitted in not_included_in_request],
        skipped_regions=skipped,
    )
