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

from fides.api.ops.api import deps
from fides.api.ops.api.v1 import scope_registry
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.api.v1.endpoints.utils import human_friendly_list
from fides.api.ops.api.v1.scope_registry import PRIVACY_EXPERIENCE_UPDATE
from fides.api.ops.models.privacy_experience import (
    ComponentType,
    DeliveryMechanism,
    PrivacyExperience,
    PrivacyExperienceConfig,
    config_incompatible_with_region,
    upsert_privacy_experiences_after_config_update,
)
from fides.api.ops.models.privacy_notice import PrivacyNoticeRegion
from fides.api.ops.oauth.utils import verify_oauth_client
from fides.api.ops.schemas.privacy_experience import (
    ExperienceConfigCreate,
    ExperienceConfigCreateOrUpdateResponse,
    ExperienceConfigResponse,
    ExperienceConfigUpdate,
)
from fides.api.ops.util.api_router import APIRouter

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


def remove_config_from_matched_experiences(
    db: Session,
    experience_config: PrivacyExperienceConfig,
    regions_to_unlink: List[PrivacyNoticeRegion],
) -> List[PrivacyExperience]:
    """Remove the config from linked PrivacyExperiences"""
    if not regions_to_unlink:
        return []

    logger.info(
        "Unlinking regions {} from Privacy Experience Config '{}'.",
        human_friendly_list([reg.value for reg in regions_to_unlink]),
        experience_config.id,
    )

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

    logger.info("Loading Experience Configs with params {}.", params)
    return fastapi_paginate(privacy_experience_config_query.all(), params=params)


def validate_experience_config_and_region_compatibility(
    db: Session,
    component_type: ComponentType,
    delivery_mechanism: DeliveryMechanism,
    regions: List[PrivacyNoticeRegion],
) -> None:
    """Validates that the supplied regions would be compatible with the proposed ExperienceConfig
    prior to making the ExperienceConfig changes and linking the Experiences for those regions.
    """
    invalid_regions: List[PrivacyNoticeRegion] = []
    for region in regions:
        if config_incompatible_with_region(
            db, component_type, delivery_mechanism, region
        ):
            invalid_regions.append(region)

    if invalid_regions:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The following regions would be incompatible with this experience: {human_friendly_list([reg.value for reg in invalid_regions])}.",
        )


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

    # Fail early if the ExperienceConfig is going to be incompatible with any of the regions
    validate_experience_config_and_region_compatibility(
        db=db,
        component_type=experience_config_data.component,
        delivery_mechanism=experience_config_data.delivery_mechanism,
        regions=new_regions,
    )

    logger.info(
        "Creating experience config of component '{}' and delivery mechanism '{}'.",
        experience_config_data.component.value,
        experience_config_data.delivery_mechanism.value,
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
    linked, unlinked, skipped = upsert_privacy_experiences_after_config_update(
        db, experience_config, new_regions
    )

    return ExperienceConfigCreateOrUpdateResponse(
        experience_config=experience_config,
        linked_regions=linked,
        unlinked_regions=unlinked,
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
    included in this request.
    """
    experience_config: PrivacyExperienceConfig = get_experience_config_or_error(
        db, experience_config_id
    )
    experience_config_data_dict: Dict = experience_config_data.dict(exclude_unset=True)
    # Pop the regions off the request
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

    # Fail early if the ExperienceConfig is going to be incompatible with any of the regions
    validate_experience_config_and_region_compatibility(
        db=db,
        component_type=dry_update.component,  # type: ignore[arg-type]
        delivery_mechanism=dry_update.delivery_mechanism,  # type: ignore[arg-type]
        regions=regions,
    )

    logger.info("Updating experience config of id '{}'.", experience_config.id)
    experience_config.update(db=db, data=experience_config_data_dict)
    db.refresh(experience_config)

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

    if regions:
        logger.info(
            "Verifying or linking regions {} to experience config '{}'.",
            human_friendly_list([reg.value for reg in regions]),
            experience_config.id,
        )
    # Upserting PrivacyExperiences based on regions specified in the request
    (
        linked,
        unlinked_for_conflict,
        skipped,
    ) = upsert_privacy_experiences_after_config_update(db, experience_config, regions)

    return ExperienceConfigCreateOrUpdateResponse(
        experience_config=experience_config,
        linked_regions=linked,
        unlinked_regions=unlinked_for_conflict
        + [omitted.region for omitted in not_included_in_request],
        skipped_regions=skipped,
    )
