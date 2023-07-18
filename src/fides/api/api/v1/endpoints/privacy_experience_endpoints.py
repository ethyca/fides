import uuid
from html import escape, unescape
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, Response
from fastapi_pagination import Page, Params
from fastapi_pagination import paginate as fastapi_paginate
from fastapi_pagination.bases import AbstractPage
from loguru import logger
from sqlalchemy.orm import Query, Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api import deps
from fides.api.models.consent_settings import ConsentSettings
from fides.api.models.privacy_experience import (
    ComponentType,
    PrivacyExperience,
    PrivacyExperienceConfig,
    cache_saved_and_served_on_consent_record,
)
from fides.api.models.privacy_notice import PrivacyNotice
from fides.api.models.privacy_preference import PreferenceType
from fides.api.models.privacy_request import ProvidedIdentity
from fides.api.schemas.privacy_experience import PrivacyExperienceResponse
from fides.api.util.api_router import APIRouter
from fides.api.util.consent_util import (
    PRIVACY_EXPERIENCE_ESCAPE_FIELDS,
    PRIVACY_NOTICE_ESCAPE_FIELDS,
    UNESCAPE_SAFESTR_HEADER,
    get_fides_user_device_id_provided_identity,
)
from fides.api.util.endpoint_utils import fides_limiter, transform_fields
from fides.api.util.tcf_util import load_tcf_data_uses
from fides.common.api.v1 import urn_registry as urls
from fides.config import CONFIG

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


def _filter_experiences_by_region_or_country(
    db: Session, region: Optional[str], experience_query: Query
) -> Query:
    """
    Return at most two privacy experiences, a privacy center experience and an overlay (regular or TCF type)
    that matches the given region. Experiences are looked up by supplied region first.  If nothing is found,
    we attempt to look up by country code.

    For example, if region was "fr_idg" and no experiences were saved under this code, we'd look again for experiences
    saved with "fr".
    """
    if not region:
        return experience_query

    region = escape(region)
    country: str = region.split("_")[0]

    overlay = PrivacyExperience.get_experience_by_region_and_component(
        db, region, ComponentType.overlay
    ) or PrivacyExperience.get_experience_by_region_and_component(
        db, country, ComponentType.overlay
    )
    privacy_center = PrivacyExperience.get_experience_by_region_and_component(
        db, region, ComponentType.privacy_center
    ) or PrivacyExperience.get_experience_by_region_and_component(
        db, country, ComponentType.privacy_center
    )
    tcf_overlay = PrivacyExperience.get_experience_by_region_and_component(
        db, region, ComponentType.tcf_overlay
    ) or PrivacyExperience.get_experience_by_region_and_component(
        db, country, ComponentType.tcf_overlay
    )

    experience_ids: List[str] = []
    consent_settings = ConsentSettings.get_or_create(db)

    if privacy_center:
        experience_ids.append(privacy_center.id)

    # Only return TCF Overlay or regular overlay here; not both
    tcf_overlay_returned: bool = False
    if consent_settings.tcf_enabled and tcf_overlay:
        experience_ids.append(tcf_overlay.id)
        tcf_overlay_returned = True

    if overlay and not tcf_overlay_returned:
        experience_ids.append(overlay.id)

    if experience_ids:
        return experience_query.filter(PrivacyExperience.id.in_(experience_ids))
    return db.query(PrivacyExperience).filter(False)


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
    region: Optional[str] = None,
    component: Optional[ComponentType] = None,
    has_notices: Optional[bool] = None,
    has_config: Optional[bool] = None,
    fides_user_device_id: Optional[str] = None,
    systems_applicable: Optional[bool] = False,
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
        try:
            uuid.UUID(fides_user_device_id, version=4)
        except ValueError:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid fides user device id format",
            )
        fides_user_provided_identity = get_fides_user_device_id_provided_identity(
            db=db, fides_user_device_id=fides_user_device_id
        )

    experience_query = db.query(PrivacyExperience)

    if show_disabled is False:
        # This field is actually stored on the PrivacyExperienceConfig.  This is a useful filter in that
        # it forces the ExperienceConfig to exist, and it has to be enabled.
        experience_query = experience_query.join(
            PrivacyExperienceConfig,
            PrivacyExperienceConfig.id == PrivacyExperience.experience_config_id,
        ).filter(PrivacyExperienceConfig.disabled.is_(False))

    if region is not None:
        experience_query = _filter_experiences_by_region_or_country(
            db=db, region=region, experience_query=experience_query
        )

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
    should_unescape = request.headers.get(UNESCAPE_SAFESTR_HEADER)
    for privacy_experience in experience_query.order_by(
        PrivacyExperience.created_at.desc()
    ):
        embed_experience_details(
            db,
            privacy_experience=privacy_experience,
            show_disabled=show_disabled,
            systems_applicable=systems_applicable,
            fides_user_provided_identity=fides_user_provided_identity,
            should_unescape=should_unescape,
        )

        # Temporarily save "show_banner" on the privacy experience object
        privacy_experience.show_banner = privacy_experience.get_should_show_banner(
            db, show_disabled
        )

        if should_unescape:
            privacy_experience.experience_config = transform_fields(
                transformation=unescape,
                model=privacy_experience.experience_config,
                fields=PRIVACY_EXPERIENCE_ESCAPE_FIELDS,
            )

        if (
            not (has_notices and not privacy_experience.privacy_notices)
            or privacy_experience.component == ComponentType.tcf_overlay
        ):
            results.append(privacy_experience)

    return fastapi_paginate(results, params=params)


def embed_experience_details(
    db: Session,
    privacy_experience: PrivacyExperience,
    show_disabled: Optional[bool],
    systems_applicable: Optional[bool],
    fides_user_provided_identity: Optional[ProvidedIdentity],
    should_unescape: Optional[bool],
):
    """At runtime, embed relevant privacy notices, tcf_data_uses, tcf_vendors,
    and tcf_features into the response body for the given Experience"""
    privacy_experience.privacy_notices = []
    privacy_experience.tcf_data_uses = []
    privacy_experience.tcf_vendors = []
    privacy_experience.tcf_features = []

    if privacy_experience.component == ComponentType.tcf_overlay:
        data_uses, vendors = load_tcf_data_uses(db)
        for record in data_uses:
            cache_saved_and_served_on_consent_record(
                db,
                record,
                fides_user_provided_identity=fides_user_provided_identity,
                preference_type=PreferenceType.data_use,
            )

        for record in vendors:
            cache_saved_and_served_on_consent_record(
                db,
                record,
                fides_user_provided_identity=fides_user_provided_identity,
                preference_type=PreferenceType.vendor,
            )

        # TODO Add features
        # Temporarily cache relevant TCF Data Uses and Vendors on the given Experience
        privacy_experience.tcf_data_uses = data_uses
        privacy_experience.tcf_vendors = vendors

    else:
        privacy_notices: List[
            PrivacyNotice
        ] = privacy_experience.get_related_privacy_notices(
            db, show_disabled, systems_applicable, fides_user_provided_identity
        )
        if should_unescape:
            privacy_notices = [
                transform_fields(
                    transformation=unescape,
                    model=notice,
                    fields=PRIVACY_NOTICE_ESCAPE_FIELDS,
                )
                for notice in privacy_notices
            ]
        # Temporarily save privacy notices on the privacy experience object
        privacy_experience.privacy_notices = privacy_notices
