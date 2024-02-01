from typing import Dict, List, Optional, Set, Union

from fastapi import Depends, HTTPException, Security
from fastapi_pagination import Page, Params
from fastapi_pagination import paginate as fastapi_paginate
from fastapi_pagination.bases import AbstractPage
from loguru import logger
from sqlalchemy.orm import Query, Session
from starlette.requests import Request
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api import deps
from fides.api.models.location_regulation_selections import LocationRegulationSelections
from fides.api.models.privacy_experience import (
    ComponentType,
    ExperienceTranslation,
    PrivacyExperience,
    PrivacyExperienceConfig,
)
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    Language,
    PrivacyNotice,
    PrivacyNoticeRegion,
)
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.privacy_experience import (
    ExperienceConfigCreate,
    ExperienceConfigResponse,
    ExperienceConfigUpdate,
)
from fides.api.schemas.privacy_experience import (
    ExperienceTranslation as ExperienceTranslationSchema,
)
from fides.api.schemas.privacy_experience import ExperienceTranslationCreate
from fides.api.util.api_router import APIRouter
from fides.api.util.consent_util import (
    UNESCAPE_SAFESTR_HEADER,
    escape_experience_fields_for_storage,
    unescape_experience_fields_for_display,
    validate_region_uniqueness_on_ux_type,
)
from fides.common.api import scope_registry
from fides.common.api.scope_registry import PRIVACY_EXPERIENCE_UPDATE
from fides.common.api.v1 import urn_registry as urls
from fides.config import CONFIG

router = APIRouter(tags=["Privacy Experience Config"], prefix=urls.V1_URL_PREFIX)


def get_configured_locations(db: Session = Depends(deps.get_db)) -> Set:
    return LocationRegulationSelections.get_selected_locations(db)


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


def get_experience_notices_or_error(
    db: Session, privacy_notice_ids: List[str]
) -> Query:
    """
    Helper method to load PrivacyNotices or throw a 404
    """
    logger.info("Finding Privacy Notices By Id '{}'", privacy_notice_ids)

    notices: Query = db.query(PrivacyNotice).filter(
        PrivacyNotice.id.in_(privacy_notice_ids)
    )
    verified_notice_ids: List[str] = [notice.id for notice in notices]

    if len(privacy_notice_ids) > len(verified_notice_ids):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Privacy Notice Id Not Found.",
        )

    return notices


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
    component: Optional[ComponentType] = None,
    region: Optional[PrivacyNoticeRegion] = None,
    request: Request,
) -> AbstractPage[PrivacyExperienceConfig]:
    """
    Returns a list of PrivacyExperienceConfig resources.  These resources have common titles, descriptions, and
    labels that can be shared between multiple experiences.
    """
    should_unescape = request.headers.get(UNESCAPE_SAFESTR_HEADER)
    privacy_experience_config_query: Query = db.query(PrivacyExperienceConfig)

    if not CONFIG.consent.tcf_enabled:
        privacy_experience_config_query = privacy_experience_config_query.filter(
            PrivacyExperienceConfig.component != ComponentType.tcf_overlay
        )

    if component:
        privacy_experience_config_query = privacy_experience_config_query.filter(
            PrivacyExperienceConfig.component == component
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
    experience_configs = privacy_experience_config_query.all()
    if should_unescape:
        for experience_config in experience_configs:
            unescape_experience_fields_for_display(experience_config)

    return fastapi_paginate(experience_configs, params=params)


@router.post(
    urls.EXPERIENCE_CONFIG,
    status_code=HTTP_201_CREATED,
    response_model=ExperienceConfigResponse,
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
) -> PrivacyExperienceConfig:
    """
    Create Experience Config, and potentially Experience Translation(s), Historical Records for auditing,
    and linking regions and privacy notices.
    """
    escape_experience_fields_for_storage(experience_config_data)

    privacy_notices: Query = get_experience_notices_or_error(
        db, experience_config_data.privacy_notice_ids or []
    )

    validate_notice_keys_or_error(privacy_notices)

    validate_translation_fields_for_ux_type(
        privacy_notices,
        experience_config_data.component,
        experience_config_data.translations,
    )

    if not experience_config_data.disabled:
        validate_region_uniqueness_on_ux_type(
            db, experience_config_data.component, experience_config_data.regions
        )

    experience_config_dict: Dict = experience_config_data.dict(exclude_unset=True)

    logger.info(
        "Creating experience config of component '{}'.",
        experience_config_data.component.value,
    )

    experience_config = PrivacyExperienceConfig.create(
        db, data=experience_config_dict, check_name=False
    )

    unescape_experience_fields_for_display(experience_config)

    return experience_config


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
    request: Request,
    configured_locations: Set = Depends(get_configured_locations),
) -> PrivacyExperienceConfig:
    """
    Returns a PrivacyExperienceConfig with embedded translations as well as its notices with config translations
    """
    logger.info("Retrieving experience config with id '{}'.", experience_config_id)
    should_unescape = request.headers.get(UNESCAPE_SAFESTR_HEADER)

    # TODO further restrict regions on locations if applicable

    experience_config = get_experience_config_or_error(db, experience_config_id)
    if should_unescape:
        unescape_experience_fields_for_display(experience_config)

    return experience_config


@router.patch(
    urls.EXPERIENCE_CONFIG_DETAIL,
    status_code=HTTP_200_OK,
    response_model=ExperienceConfigResponse,
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
) -> PrivacyExperienceConfig:
    """
    Update Experience Config and link associated resources.

    All regions, translations, and privacy notices that you want linked to the Experience Config need
    to be passed in through the request, regardless of whether you're editing or they will be unlinked.
    """
    experience_config: PrivacyExperienceConfig = get_experience_config_or_error(
        db, experience_config_id
    )

    privacy_notices: Query = get_experience_notices_or_error(
        db, experience_config_data.privacy_notice_ids or []
    )

    validate_notice_keys_or_error(privacy_notices)

    escape_experience_fields_for_storage(experience_config_data)

    experience_config_data_dict: Dict = experience_config_data.dict(exclude_unset=True)

    # Because we're allowing patch updates here, first do a dry update and make sure the experience
    # config wouldn't be put in a bad state.
    dry_update: PrivacyExperienceConfig = experience_config.dry_update(
        data=experience_config_data_dict
    )
    dry_update_translations: List[
        ExperienceTranslation
    ] = experience_config.dry_update_translations(
        [
            translation.dict(exclude_unset=True)
            for translation in experience_config_data.translations
        ]
    )

    try:
        dry_update.translations = dry_update_translations
        ExperienceConfigCreate.from_orm(dry_update)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            # pylint: disable=no-member
            detail=exc.errors(),  # type: ignore
        )

    validate_translation_fields_for_ux_type(
        privacy_notices, dry_update.component, dry_update_translations
    )

    if not dry_update.disabled:
        validate_region_uniqueness_on_ux_type(
            db,
            ux_type=experience_config.component,
            regions=experience_config_data.regions,
            excluded_config=experience_config_id,
        )

    logger.info("Updating experience config of id '{}'.", experience_config.id)
    experience_config.update(db=db, data=experience_config_data_dict)
    db.refresh(experience_config)

    unescape_experience_fields_for_display(experience_config)

    return experience_config


def validate_notice_keys_or_error(privacy_notices: Query) -> None:
    """Validate notice keys assigned to Privacy Experience Config do not overlap"""
    if not privacy_notices.first():
        return

    notice_keys: List[str] = [notice.notice_key for notice in privacy_notices]

    if len(notice_keys) > len(set(notice_keys)):
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Duplicate notice keys detected",
        )


def validate_translation_fields_for_ux_type(
    privacy_notices: Query,
    component_type: ComponentType,
    translations: Union[
        List[ExperienceTranslation],
        List[ExperienceTranslationSchema],
        List[ExperienceTranslationCreate],
    ],
) -> None:
    """Validate translations that are required to be defined for various UX types

    While we could validate some of these with a Pydantic validator, because we need the privacy notice consent mechanisms
    from the database for others, let's just define all this in one place here.
    """
    required_fields: List[str] = []

    if component_type == ComponentType.banner:
        if privacy_notices.filter(
            PrivacyNotice.consent_mechanism.in_(
                [ConsentMechanism.opt_in, ConsentMechanism.opt_out]
            )
        ).first():
            required_fields = [
                "title",
                "description",
                "accept_button_label",
                "reject_button_label",
            ]

        if privacy_notices.filter(
            PrivacyNotice.consent_mechanism == ConsentMechanism.notice_only
        ).first():
            required_fields = ["title", "description", "acknowledge_button_label"]

    if component_type in [ComponentType.overlay, ComponentType.tcf_overlay]:
        required_fields = [
            "title",
            "description",
            "accept_button_label",
            "reject_button_label",
            "privacy_preferences_link_label",
        ]

    if component_type == ComponentType.modal:
        required_fields = [
            "title",
            "description",
            "accept_button_label",
            "reject_button_label",
        ]

    for translation in translations or []:
        for field in required_fields:
            if not getattr(translation, field, None):
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Missing '{field}' needed for language '{translation.language.value if isinstance(translation.language, Language) else translation.language}' for UX type '{component_type.value}'.",
                )
