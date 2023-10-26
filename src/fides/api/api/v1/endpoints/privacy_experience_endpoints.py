import asyncio
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
from fides.api.models.privacy_experience import (
    ComponentType,
    PrivacyExperience,
    PrivacyExperienceConfig,
)
from fides.api.models.privacy_notice import PrivacyNotice
from fides.api.models.privacy_request import ProvidedIdentity
from fides.api.schemas.privacy_experience import (
    PrivacyExperienceMetaResponse,
    PrivacyExperienceResponse,
)
from fides.api.util.api_router import APIRouter
from fides.api.util.consent_util import (
    PRIVACY_EXPERIENCE_ESCAPE_FIELDS,
    PRIVACY_NOTICE_ESCAPE_FIELDS,
    UNESCAPE_SAFESTR_HEADER,
    get_fides_user_device_id_provided_identity,
)
from fides.api.util.endpoint_utils import fides_limiter, transform_fields
from fides.api.util.tcf.experience_meta import build_experience_tcf_meta
from fides.api.util.tcf.tcf_experience_contents import (
    TCF_SECTION_MAPPING,
    TCFExperienceContents,
    get_tcf_contents,
    load_gvl,
)
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


def _filter_experiences_by_component(
    component: ComponentType, experience_query: Query
) -> Query:
    """
    Filters privacy experiences by component

    Intentionally relaxes what is returned when querying for "overlay", by returning both types of overlays.
    This way the frontend doesn't have to know which type of overlay, regular or tcf, just that it is an overlay.
    """
    component_search_map: Dict = {
        ComponentType.overlay: [ComponentType.overlay, ComponentType.tcf_overlay]
    }
    return experience_query.filter(
        PrivacyExperience.component.in_(
            component_search_map.get(component, [component])
        )
    )


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
    if CONFIG.consent.tcf_enabled and tcf_overlay:
        experience_ids.append(tcf_overlay.id)
    elif overlay:
        experience_ids.append(overlay.id)

    if experience_ids:
        return experience_query.filter(PrivacyExperience.id.in_(experience_ids))
    return db.query(PrivacyExperience).filter(False)


@router.get(
    urls.PRIVACY_EXPERIENCE_META,
    status_code=HTTP_200_OK,
    response_model=Page[PrivacyExperienceMetaResponse],
)
@fides_limiter.limit(CONFIG.security.public_request_rate_limit)
async def get_privacy_experience_meta(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    region: Optional[str] = None,
    component: Optional[ComponentType] = None,
    request: Request,  # required for rate limiting
    response: Response,  # required for rate limiting
) -> AbstractPage[PrivacyExperience]:
    """Minimal Developer Friendly Privacy Experience endpoint that returns only the meta object,
    the component, and the region."""

    logger.info("Fetching meta info for Experiences '{}'", params)

    await asyncio.sleep(delay=0.001)
    experience_query: Query = db.query(PrivacyExperience)

    await asyncio.sleep(delay=0.001)
    if region is not None:
        experience_query = _filter_experiences_by_region_or_country(
            db=db, region=region, experience_query=experience_query
        )

    await asyncio.sleep(delay=0.001)
    if component is not None:
        experience_query = _filter_experiences_by_component(component, experience_query)

    await asyncio.sleep(delay=0.001)
    # TCF contents are the same across all EEA regions, so we can build this once.
    base_tcf_contents: TCFExperienceContents = get_tcf_contents(db)

    tcf_meta: Optional[Dict] = None
    for (
        tcf_section_name,
        _,
    ) in TCF_SECTION_MAPPING.items():
        if getattr(base_tcf_contents, tcf_section_name):
            # TCF Experience meta is also the same across all EEA regions. Only build meta if there is TCF
            # content under at least one section.
            tcf_meta = build_experience_tcf_meta(base_tcf_contents)
            break

    results: List[PrivacyExperience] = []
    for experience in experience_query:
        if experience.component == ComponentType.tcf_overlay:
            # Attach meta for TCF Experiences only.  We don't yet build meta info for non-TCF experiences.
            experience.meta = tcf_meta
        results.append(experience)

    return fastapi_paginate(results, params=params)


@router.get(
    urls.PRIVACY_EXPERIENCE,
    status_code=HTTP_200_OK,
    response_model=Page[PrivacyExperienceResponse],
)
@fides_limiter.limit(CONFIG.security.public_request_rate_limit)
async def privacy_experience_list(
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
    include_gvl: Optional[bool] = False,
    include_meta: Optional[bool] = False,
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
    :param include_gvl: Embeds gvl.json in the response provided we also have TCF content
    :param include_meta: If True, returns TCF Experience meta if applicable
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

    await asyncio.sleep(delay=0.001)
    experience_query = db.query(PrivacyExperience)

    if show_disabled is False:
        # This field is actually stored on the PrivacyExperienceConfig.  This is a useful filter in that
        # it forces the ExperienceConfig to exist, and it has to be enabled.
        experience_query = experience_query.join(
            PrivacyExperienceConfig,
            PrivacyExperienceConfig.id == PrivacyExperience.experience_config_id,
        ).filter(PrivacyExperienceConfig.disabled.is_(False))

    await asyncio.sleep(delay=0.001)
    if region is not None:
        experience_query = _filter_experiences_by_region_or_country(
            db=db, region=region, experience_query=experience_query
        )

    await asyncio.sleep(delay=0.001)
    if component is not None:
        experience_query = _filter_experiences_by_component(component, experience_query)

    await asyncio.sleep(delay=0.001)
    if has_config is True:
        experience_query = experience_query.filter(
            PrivacyExperience.experience_config_id.isnot(None)
        )
    await asyncio.sleep(delay=0.001)
    if has_config is False:
        experience_query = experience_query.filter(
            PrivacyExperience.experience_config_id.is_(None)
        )

    results: List[PrivacyExperience] = []
    should_unescape: Optional[str] = request.headers.get(UNESCAPE_SAFESTR_HEADER)

    # Builds TCF Experience Contents once here, in case multiple TCF Experiences are requested
    await asyncio.sleep(delay=0.001)
    base_tcf_contents: TCFExperienceContents = get_tcf_contents(db)

    await asyncio.sleep(delay=0.001)
    for privacy_experience in experience_query.order_by(
        PrivacyExperience.created_at.desc()
    ):
        await asyncio.sleep(delay=0.001)
        content_exists: bool = embed_experience_details(
            db,
            privacy_experience=privacy_experience,
            show_disabled=show_disabled,
            systems_applicable=systems_applicable,
            fides_user_provided_identity=fides_user_provided_identity,
            should_unescape=should_unescape,
            include_gvl=include_gvl,
            include_meta=include_meta,
            base_tcf_contents=base_tcf_contents,
        )

        if content_required and not content_exists:
            continue

        # Temporarily save "show_banner" on the privacy experience object
        await asyncio.sleep(delay=0.001)
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
    include_gvl: Optional[bool],
    include_meta: Optional[bool],
    base_tcf_contents: TCFExperienceContents,
) -> bool:
    """
    Embed the contents of the PrivacyExperience at runtime. Adds Privacy Notices or TCF contents if applicable.

    The PrivacyExperience is updated in-place, and this method returns whether there is content
    on this experience.
    """
    # Reset any temporary cached items just in case
    privacy_experience.privacy_notices = []
    privacy_experience.meta = {}
    privacy_experience.gvl = {}
    for component in TCF_SECTION_MAPPING:
        setattr(privacy_experience, component, [])

    # Updates Privacy Experience in-place with TCF Contents if applicable, and then returns
    # if TCF contents exist
    has_tcf_contents: bool = privacy_experience.update_with_tcf_contents(
        db, base_tcf_contents, fides_user_provided_identity
    )

    if has_tcf_contents:
        if include_meta:
            privacy_experience.meta = build_experience_tcf_meta(base_tcf_contents)
        if include_gvl:
            privacy_experience.gvl = load_gvl()

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
