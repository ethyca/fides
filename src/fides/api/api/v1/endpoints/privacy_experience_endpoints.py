import uuid
from html import escape, unescape
from typing import Dict, List, Optional

from fastapi import Depends, HTTPException
from fastapi import Query as FastAPIQuery
from fastapi import Request, Response
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
)
from fides.api.models.privacy_notice import PrivacyNotice
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
from fides.api.util.tcf_util import TCF_COMPONENT_MAPPING, TCFExperienceContents
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
    Return at most two privacy experiences: a privacy center experience and an overlay (regular or TCF type)
    that matches the given region. Experiences are looked up by supplied region first.  If nothing is found,
    we attempt to look up by country code.

    For example, if region was "fr_idg" and no experiences were saved under this code, we'd look again for experiences
    saved with "fr".
    """
    if not region:
        return experience_query

    cleaned_region: str = escape(region).replace("-", "_").lower()
    country: str = cleaned_region.split("_")[0]

    overlay: Optional[
        PrivacyExperience
    ] = PrivacyExperience.get_experience_by_region_and_component(
        db, cleaned_region, ComponentType.overlay
    ) or PrivacyExperience.get_experience_by_region_and_component(
        db, country, ComponentType.overlay
    )
    privacy_center: Optional[
        PrivacyExperience
    ] = PrivacyExperience.get_experience_by_region_and_component(
        db, cleaned_region, ComponentType.privacy_center
    ) or PrivacyExperience.get_experience_by_region_and_component(
        db, country, ComponentType.privacy_center
    )
    tcf_overlay: Optional[
        PrivacyExperience
    ] = PrivacyExperience.get_experience_by_region_and_component(
        db, cleaned_region, ComponentType.tcf_overlay
    ) or PrivacyExperience.get_experience_by_region_and_component(
        db, country, ComponentType.tcf_overlay
    )

    experience_ids: List[str] = []

    if privacy_center:
        experience_ids.append(privacy_center.id)

    # Only return TCF overlay or a regular overlay here; not both
    consent_settings: ConsentSettings = ConsentSettings.get_or_create_with_defaults(db)
    if consent_settings.tcf_enabled and tcf_overlay:
        experience_ids.append(tcf_overlay.id)
    elif overlay:
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
    content_required: Optional[bool] = FastAPIQuery(default=None, alias="has_notices"),
    has_config: Optional[bool] = None,
    fides_user_device_id: Optional[str] = None,
    systems_applicable: Optional[bool] = False,
    request: Request,  # required for rate limiting
    response: Response,  # required for rate limiting
) -> AbstractPage[PrivacyExperience]:
    """
    Public endpoint that returns a list of PrivacyExperience records for individual regions with
    relevant privacy notices or tcf contents embedded in the response.

    'show_disabled' query params are passed along to further filter
    notices as well.

    :param db:
    :param params:
    :param show_disabled: If False, returns only enabled Experiences and Notices
    :param region: Return the Experiences for the given region
    :param component: Returns Experiences of the given component type
    :param content_required: Return if the Experience has content. (Alias for has_notices query_param)
    :param has_config: If True, returns Experiences with copy. If False, returns just Experiences without copy.
    :param fides_user_device_id: Supplement the response with current saved preferences of the given user
    :param systems_applicable: Only return embedded Notices associated with systems.
    :param request:
    :param response:
    :return:
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
        # Intentionally relaxes what is returned when querying for "overlay", by returning both types of overlays.
        # This way the frontend doesn't have to know which type of overlay, regular or tcf, just that it is an overlay.
        component_search_map: Dict = {
            ComponentType.overlay: [ComponentType.overlay, ComponentType.tcf_overlay]
        }
        experience_query = experience_query.filter(
            PrivacyExperience.component.in_(
                component_search_map.get(component, [component])
            )
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
    should_unescape: Optional[str] = request.headers.get(UNESCAPE_SAFESTR_HEADER)
    for privacy_experience in experience_query.order_by(
        PrivacyExperience.created_at.desc()
    ):
        content_exists: bool = embed_experience_details(
            db,
            privacy_experience=privacy_experience,
            show_disabled=show_disabled,
            systems_applicable=systems_applicable,
            fides_user_provided_identity=fides_user_provided_identity,
            should_unescape=should_unescape,
        )

        if content_required and not content_exists:
            continue

        # Temporarily save "show_banner" on the privacy experience object
        privacy_experience.show_banner = privacy_experience.get_should_show_banner(
            db, show_disabled
        )

        if should_unescape:
            # Unescape the experience config details
            privacy_experience.experience_config = transform_fields(
                transformation=unescape,
                model=privacy_experience.experience_config,
                fields=PRIVACY_EXPERIENCE_ESCAPE_FIELDS,
            )

        results.append(privacy_experience)

    return fastapi_paginate(results, params=params)


def embed_experience_details(
    db: Session,
    privacy_experience: PrivacyExperience,
    show_disabled: Optional[bool],
    systems_applicable: Optional[bool],
    fides_user_provided_identity: Optional[ProvidedIdentity],
    should_unescape: Optional[str],
) -> bool:
    """
    Embed the contents of the PrivacyExperience at runtime. Adds Privacy Notices or TCF contents if applicable.

    The PrivacyExperience is updated in-place, and this method returns whether there is content
    on this experience.
    """
    # Reset any temporary cached items just in case
    privacy_experience.privacy_notices = []
    for component in TCF_COMPONENT_MAPPING:
        setattr(privacy_experience, component, [])

    # Fetch the base TCF Contents
    tcf_contents: TCFExperienceContents = privacy_experience.get_related_tcf_contents(
        db, fides_user_provided_identity
    )
    has_tcf_contents: bool = any(
        getattr(tcf_contents, component) for component in TCF_COMPONENT_MAPPING
    )
    # Add fetched TCF contents to the Privacy Experience if applicable
    for component in TCF_COMPONENT_MAPPING:
        setattr(privacy_experience, component, getattr(tcf_contents, component))

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
    # Add Privacy Notices to the Experience if applicable
    privacy_experience.privacy_notices = privacy_notices

    return bool(privacy_notices) or has_tcf_contents
