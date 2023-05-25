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
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api import deps
from fides.api.api.v1 import scope_registry
from fides.api.api.v1 import urn_registry as urls
from fides.api.api.v1.endpoints.utils import human_friendly_list
from fides.api.api.v1.scope_registry import PRIVACY_EXPERIENCE_UPDATE
from fides.api.models.privacy_experience import (
    ComponentType,
    PrivacyExperience,
    PrivacyExperienceConfig,
    upsert_privacy_experiences_after_config_update,
)
from fides.api.models.privacy_notice import PrivacyNoticeRegion
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.privacy_experience import (
    ExperienceConfigCreate,
    ExperienceConfigCreateOrUpdateResponse,
    ExperienceConfigResponse,
    ExperienceConfigUpdate,
)
from fides.api.util.api_router import APIRouter

router = APIRouter(tags=["Privacy Experience Config"], prefix=urls.V1_URL_PREFIX)


def get_experience_config_or_error(
    db: Session, experience_config_id: str
) -> PrivacyExperienceConfig:
    """
    Helper method to load ExperienceConfig or throw a 404
    """
    logger.info("Finding Privacy Experience Config with id '{}'", experience_config_id)
    experience_config = PrivacyExperienceConfig.get(
        db=db, object_id=experience_config_id
    )
    if not experience_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No Privacy Experience Config found for id '{experience_config_id}'.",
        )

    return experience_config


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

    logger.info("Loading Experience Configs with params {}.", params)
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
    Create Experience Config and then attempt to upsert Experiences and link to ExperienceConfig
    """
    experience_config_dict: Dict = experience_config_data.dict(exclude_unset=True)
    # Pop the regions off the request
    new_regions: List[PrivacyNoticeRegion] = experience_config_dict.pop("regions")

    logger.info(
        "Creating experience config of component '{}'.",
        experience_config_data.component.value,
    )
    experience_config = PrivacyExperienceConfig.create(
        db, data=experience_config_dict, check_name=False
    )

    if new_regions:
        logger.info(
            "Linking regions: {} to experience config '{}'",
            human_friendly_list([reg.value for reg in new_regions]),
            experience_config.id,
        )
    linked, unlinked = upsert_privacy_experiences_after_config_update(
        db, experience_config, new_regions
    )

    return ExperienceConfigCreateOrUpdateResponse(
        experience_config=experience_config,
        linked_regions=linked,
        unlinked_regions=unlinked,
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
    logger.info("Retrieving experience config with id '{}'.", experience_config_id)
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
    Update Experience Config and then attempt to upsert Experiences and link back to ExperienceConfig.

    All regions that should be linked to this ExperienceConfig (or remain linked) need to be
    included in this request.  If you want to ignore regions being updated, pass in None for regions.
    If you want to remove regions, pass in an empty list.
    """
    experience_config: PrivacyExperienceConfig = get_experience_config_or_error(
        db, experience_config_id
    )
    experience_config_data_dict: Dict = experience_config_data.dict(exclude_unset=True)
    # Pop the regions off the request
    regions: Optional[List[PrivacyNoticeRegion]] = experience_config_data_dict.pop(
        "regions", None
    )

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

    logger.info("Updating experience config of id '{}'.", experience_config.id)
    experience_config.update(db=db, data=experience_config_data_dict)
    db.refresh(experience_config)

    linked: List[PrivacyNoticeRegion] = []
    unlinked_regions: List[PrivacyNoticeRegion] = []
    if (
        regions is not None
    ):  # If regions list is not in the request, we skip linking/unlinking regions
        logger.info(
            "Verifying or linking regions {} to experience config '{}'.",
            human_friendly_list([reg.value for reg in regions]),
            experience_config.id,
        )
        # Upserting PrivacyExperiences based on regions specified in the request.
        # Valid Privacy Experiences will be linked via FK to the given Experience Config.
        (
            linked,
            unlinked_regions,
        ) = upsert_privacy_experiences_after_config_update(
            db, experience_config, regions
        )

        logger.info(
            "Unlinking regions {} from Privacy Experience Config '{}'.",
            human_friendly_list([reg.value for reg in unlinked_regions]),
            experience_config.id,
        )

    return ExperienceConfigCreateOrUpdateResponse(
        experience_config=experience_config,
        linked_regions=linked,
        unlinked_regions=unlinked_regions,
    )
