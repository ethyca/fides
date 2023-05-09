from typing import Dict, List, Optional, Set, Tuple

from fastapi import Depends, HTTPException, Security
from fastapi_pagination import Page, Params
from fastapi_pagination import paginate as fastapi_paginate
from fastapi_pagination.bases import AbstractPage
from loguru import logger
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
from fides.api.ops.api.v1.scope_registry import PRIVACY_EXPERIENCE_UPDATE
from fides.api.ops.models.privacy_experience import (
    ComponentType,
    DeliveryMechanism,
    ExperienceLanguage,
    PrivacyExperience,
    get_privacy_notices_by_region_and_component,
)
from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    PrivacyNotice,
    PrivacyNoticeRegion,
)
from fides.api.ops.oauth.utils import verify_oauth_client
from fides.api.ops.schemas.privacy_experience import (
    ExperienceLanguageCreate,
    ExperienceLanguageCreateOrUpdateResponse,
    ExperienceLanguageUpdate,
    PrivacyExperienceResponse,
    PrivacyExperienceWithId,
)
from fides.api.ops.util.api_router import APIRouter

router = APIRouter(tags=["Privacy Experience"], prefix=urls.V1_URL_PREFIX)


def get_experience_language_or_error(
    db: Session, experience_language_id: str
) -> ExperienceLanguage:
    """
    Helper method to load ExperienceLanguage or throw a 404
    """
    logger.info("Finding ExperienceLanguage with id '{}'", experience_language_id)
    experience_language = ExperienceLanguage.get(
        db=db, object_id=experience_language_id
    )
    if not experience_language:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No ExperienceLanguage found for id '{experience_language_id}'.",
        )

    return experience_language


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
    Get privacy experience with embedded notices.

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


def remove_language_from_experience(
    db: Session,
    experience_language: ExperienceLanguage,
    regions_to_unlink: List[PrivacyNoticeRegion],
) -> List[PrivacyExperience]:
    """Remove the language from a PrivacyExperience"""
    experiences_to_unlink: List[PrivacyExperience] = experience_language.experiences.filter(  # type: ignore[call-arg]
        PrivacyExperience.region.in_(regions_to_unlink)
    ).all()
    for experience in experiences_to_unlink:
        experience.unlink_privacy_experience_language(db)
    return experiences_to_unlink


def upsert_privacy_experiences(
    db: Session,
    experience_language: ExperienceLanguage,
    regions: List[PrivacyNoticeRegion],
) -> Tuple[
    List[PrivacyNoticeRegion], List[PrivacyNoticeRegion], List[PrivacyNoticeRegion]
]:
    """Add, update, or remove privacy experiences that are attached to given experience language"""
    added_regions: List[PrivacyNoticeRegion] = []
    removed_regions: List[PrivacyNoticeRegion] = []
    skipped_regions: List[PrivacyNoticeRegion] = []

    for region in regions:
        (
            overlay_experience,
            privacy_center_experience,
        ) = PrivacyExperience.get_experiences_by_region(db, region)
        existing_experience: Optional[PrivacyExperience] = (
            overlay_experience
            if experience_language.component == ComponentType.overlay
            else privacy_center_experience
        )

        if (
            experience_language.component == ComponentType.overlay
            and experience_language.delivery_mechanism == DeliveryMechanism.link
        ):
            if privacy_center_experience:
                logger.info(
                    "Two experiences for the same region '{}' cannot be delivered via link.",
                    region.value,
                )
                if existing_experience:
                    existing_experience.unlink_privacy_experience_language(db)
                    removed_regions.append(region)
                else:
                    skipped_regions.append(region)
                continue

            if (
                get_privacy_notices_by_region_and_component(
                    db, region, experience_language.component  # type: ignore[arg-type]
                )
                .filter(
                    PrivacyNotice.consent_mechanism.in_(
                        [ConsentMechanism.opt_in, ConsentMechanism.notice_only]
                    )
                )
                .first()
            ):
                logger.info(
                    "Region '{}' contains opt-in or notice-only notices that must be delivered via a banner not a link.",
                    region,
                )
                if existing_experience:
                    existing_experience.unlink_privacy_experience_language(db)
                    removed_regions.append(region)
                else:
                    skipped_regions.append(region)
                continue

        data = {
            "component": experience_language.component,
            "delivery_mechanism": experience_language.delivery_mechanism,
            "region": region,
            "experience_language_id": experience_language.id,
            "experience_language_history_id": experience_language.experience_language_history_id,
            "disabled": experience_language.disabled,
        }

        if existing_experience:
            if existing_experience.experience_language_id != experience_language.id:
                added_regions.append(region)
            existing_experience.update(db, data=data)

        else:
            PrivacyExperience.create(
                db,
                data=data,
            )
            added_regions.append(region)
    return added_regions, removed_regions, skipped_regions


@router.post(
    urls.EXPERIENCE_LANGUAGE,
    status_code=HTTP_201_CREATED,
    response_model=ExperienceLanguageCreateOrUpdateResponse,
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
def experience_language_create(
    *,
    db: Session = Depends(deps.get_db),
    experience_data: ExperienceLanguageCreate,
) -> ExperienceLanguageCreateOrUpdateResponse:
    """
    Create Experience Language and then attempt to upsert Experiences and link to ExperienceLanguage
    """
    logger.info(
        "Creating experience language of component {} and delivery mechanism {} for regions {}.",
        experience_data.component,
        experience_data.delivery_mechanism,
        experience_data.regions,
    )
    experience_language_data: Dict = experience_data.dict(exclude_unset=True)
    new_regions: List[PrivacyNoticeRegion] = experience_language_data.pop("regions")

    experience_language = ExperienceLanguage.create(
        db, data=experience_language_data, check_name=False
    )

    added, removed, skipped = upsert_privacy_experiences(
        db, experience_language, new_regions
    )

    return ExperienceLanguageCreateOrUpdateResponse(
        experience_language=experience_language,
        added_regions=added,
        removed_regions=removed,
        skipped_regions=skipped,
    )


@router.patch(
    urls.EXPERIENCE_LANGUAGE_DETAIL,
    status_code=HTTP_200_OK,
    response_model=ExperienceLanguageCreateOrUpdateResponse,
    dependencies=[
        Security(
            verify_oauth_client,
            scopes=[
                PRIVACY_EXPERIENCE_UPDATE,
            ],
        )
    ],
)
def experience_language_update(
    *,
    db: Session = Depends(deps.get_db),
    experience_language_id: str,
    experience_data: ExperienceLanguageUpdate,
) -> ExperienceLanguageCreateOrUpdateResponse:
    """
    Update Experience Language and then attempt to upsert Experiences and link back to ExperienceLanguage
    """
    experience_language: ExperienceLanguage = get_experience_language_or_error(
        db, experience_language_id
    )
    experience_language_data: Dict = experience_data.dict(exclude_unset=True)
    regions: List[PrivacyNoticeRegion] = experience_language_data.pop("regions")

    # Because we're allowing patch updates here, first do a dry update and make sure the experience
    # language wouldn't be put in a bad state.
    dry_update: ExperienceLanguage = experience_language.dry_update(
        data=experience_language_data
    )
    try:
        ExperienceLanguageCreate.from_orm(dry_update)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),  # type: ignore
        )

    logger.info("Updating experience language of id '{}'", experience_language.id)
    experience_language.update(db=db, data=experience_language_data)

    # Upserting PrivacyExperiences based on regions specified in the request
    current_regions: List[PrivacyNoticeRegion] = experience_language.regions
    not_included_in_request: List[PrivacyExperience] = remove_language_from_experience(
        db,
        experience_language,
        [
            PrivacyNoticeRegion(reg)
            for reg in {reg.value for reg in current_regions}.difference(
                {reg.value for reg in regions}
            )
        ],
    )

    added, removed_for_conflict, skipped = upsert_privacy_experiences(
        db, experience_language, regions
    )
    return ExperienceLanguageCreateOrUpdateResponse(
        experience_language=experience_language,
        added_regions=added,
        removed_regions=removed_for_conflict
        + [omitted.region for omitted in not_included_in_request],
        skipped_regions=skipped,
    )
