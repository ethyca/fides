from typing import List, Set

from sqlalchemy.orm import Session
from fides.api.ops.models.privacy_experience import ComponentType
from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    PrivacyNotice,
    PrivacyNoticeRegion,
)
from fides.api.ops.schemas.privacy_experience import (
    PrivacyExperience as PrivacyExperienceSchema,
)


def get_unique_regions(privacy_notices: List[PrivacyNotice]) -> Set[str]:
    """Consolidates a list of privacy notice regions into a set of unique regions.  Combines "eu" regions into one region."""
    unique_regions: Set[str] = set()
    for notice in privacy_notices:
        for region in notice.regions:
            region_str = "eu" if region.value.startswith("eu") else region.value  # type: ignore[attr-defined]
            unique_regions.add(region_str)

    return unique_regions


def region_str_to_privacy_notice_regions_list(
    region_str: str,
) -> List[PrivacyNoticeRegion]:
    """
    Takes a region str and turns it into a list of PrivacyNoticeRegions. If "eu" is supplied, split this out into
    all eu regions.
    """
    return (
        [region for region in PrivacyNoticeRegion if region.value.startswith("eu")]
        if region_str == "eu"
        else [PrivacyNoticeRegion(region_str)]
    )


def _stage_privacy_center_experiences(
    component_type: ComponentType,
    regions: Set[str],
    pending_experiences: List[PrivacyExperienceSchema],
    combine_into_one: bool = False,
) -> None:
    """Stages privacy experiences schemas with the given component type and regions. Updates pending_experiences in place.
    Can combine all the regions into one schema, or create a separate schema for each region.

    Effectively treats the "eu" as the same region.
    """
    experience_regions: List[PrivacyNoticeRegion] = []
    for region in regions:
        if combine_into_one:
            expanded_regions = region_str_to_privacy_notice_regions_list(region)
            experience_regions.extend(expanded_regions)

        else:
            experience_regions = region_str_to_privacy_notice_regions_list(region)
            pending_experiences.append(
                PrivacyExperienceSchema(
                    component=component_type, regions=experience_regions
                )
            )

    if combine_into_one:
        pending_experiences.append(
            PrivacyExperienceSchema(
                component=component_type, regions=experience_regions
            )
        )


def create_privacy_experiences_from_notices(
    db: Session,
) -> List[PrivacyExperienceSchema]:
    """Stage privacy experiences schemas from privacy notices"""
    pending_experiences: List[PrivacyExperienceSchema] = []

    unique_opt_in_overlay_regions: Set[str] = get_unique_regions(
        db.query(PrivacyNotice).filter(  # type: ignore[arg-type]
            PrivacyNotice.consent_mechanism == ConsentMechanism.opt_in,
            PrivacyNotice.displayed_in_overlay.is_(True),
        )
    )
    _stage_privacy_center_experiences(
        component_type=ComponentType.overlay,
        regions=unique_opt_in_overlay_regions,
        pending_experiences=pending_experiences,
        combine_into_one=False,
    )

    unique_opt_out_overlay_regions: Set[str] = get_unique_regions(
        db.query(PrivacyNotice).filter(  # type: ignore[arg-type]
            PrivacyNotice.consent_mechanism == ConsentMechanism.opt_out,
            PrivacyNotice.displayed_in_overlay.is_(True),
        )
    )
    new_regions = unique_opt_out_overlay_regions - unique_opt_in_overlay_regions
    _stage_privacy_center_experiences(
        component_type=ComponentType.overlay,
        regions=new_regions,
        pending_experiences=pending_experiences,
        combine_into_one=True,
    )

    unique_notice_only_regions: Set[str] = get_unique_regions(
        db.query(PrivacyNotice).filter(  # type: ignore[arg-type]
            PrivacyNotice.consent_mechanism == ConsentMechanism.notice_only,
        )
    )
    new_regions = unique_notice_only_regions - (
        unique_opt_out_overlay_regions | unique_opt_in_overlay_regions
    )
    _stage_privacy_center_experiences(
        component_type=ComponentType.overlay,
        regions=new_regions,
        pending_experiences=pending_experiences,
        combine_into_one=True,
    )

    unique_privacy_center_regions: Set[str] = get_unique_regions(
        db.query(PrivacyNotice).filter(  # type: ignore[arg-type]
            PrivacyNotice.displayed_in_privacy_center.is_(True)
        )
    )
    _stage_privacy_center_experiences(
        component_type=ComponentType.privacy_center,
        regions=unique_privacy_center_regions,
        pending_experiences=pending_experiences,
        combine_into_one=True,
    )
    return pending_experiences
