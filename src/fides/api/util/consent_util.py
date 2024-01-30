from html import escape
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Type, Union

import yaml
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.common_exceptions import ValidationError
from fides.api.custom_types import SafeStr
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_experience import (
    ComponentType,
    PrivacyExperience,
    PrivacyExperienceConfig,
    upsert_privacy_experiences_after_notice_update,
)
from fides.api.models.privacy_notice import (
    PRIVACY_NOTICE_TYPE,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeRegion,
    PrivacyNoticeTemplate,
    UserConsentPreference,
    check_conflicting_notice_keys,
)
from fides.api.models.privacy_preference_v2 import PrivacyPreferenceHistory
from fides.api.models.privacy_request import (
    ExecutionLogStatus,
    PrivacyRequest,
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.models.sql_models import DataUse, System  # type: ignore[attr-defined]
from fides.api.models.tcf_purpose_overrides import TCFPurposeOverride
from fides.api.schemas.privacy_experience import ExperienceConfigCreateWithId
from fides.api.schemas.privacy_notice import PrivacyNoticeCreation, PrivacyNoticeWithId
from fides.api.schemas.redis_cache import Identity
from fides.api.util.endpoint_utils import transform_fields
from fides.config.helpers import load_file

PRIVACY_NOTICE_ESCAPE_FIELDS = ["name", "description", "internal_description"]
PRIVACY_EXPERIENCE_ESCAPE_FIELDS = [
    "accept_button_label",
    "acknowledge_button_label",
    "banner_description",
    "banner_title",
    "description",
    "privacy_policy_link_label",
    "privacy_policy_url",
    "privacy_preferences_link_label",
    "reject_button_label",
    "save_button_label",
    "title",
]
UNESCAPE_SAFESTR_HEADER = "unescape-safestr"


def filter_privacy_preferences_for_propagation(
    system: Optional[System],
    privacy_preferences: List[PrivacyPreferenceHistory],
) -> List[PrivacyPreferenceHistory]:
    """Filter privacy preferences on a privacy request to just the ones that should be considered for third party
    consent propagation.

    Only applies to preferences saved for privacy notices here, not against individual TCF components.
    """

    propagatable_preferences: List[PrivacyPreferenceHistory] = [
        pref
        for pref in privacy_preferences
        if pref.privacy_notice_history
        and pref.privacy_notice_history.enforcement_level
        == EnforcementLevel.system_wide
        and (
            pref.preference
            and pref.preference
            in [UserConsentPreference.opt_in, UserConsentPreference.opt_out]
        )
    ]

    if not system:
        return propagatable_preferences

    filtered_on_use: List[PrivacyPreferenceHistory] = []
    for pref in propagatable_preferences:
        if (
            pref.privacy_notice_history
            and pref.privacy_notice_history.applies_to_system(system)
        ):
            filtered_on_use.append(pref)
    return filtered_on_use


def should_opt_in_to_service(
    system: Optional[System], privacy_request: PrivacyRequest
) -> Tuple[Optional[bool], List[PrivacyPreferenceHistory]]:
    """
    For SaaS Connectors, examine the Privacy Preferences and collapse this information into a single should we opt in? (True),
    should we opt out? (False) or should we do nothing? (None).

    Email connectors should instead call "filter_privacy_preferences_for_propagation" directly, since we can have preferences with
    conflicting opt in/opt out values for those connector types.

    Also return filtered preferences here so we can cache affected systems and/or secondary identifiers directly on these
    filtered preferences for consent reporting.

    - If using the old workflow (privacyrequest.consent_preferences), return True if all attached consent preferences
    are opt in, otherwise False.  System check is ignored.

    - If using the new workflow (privacyrequest.privacy_preferences), there is more filtering here.  Privacy Preferences
    must have an enforcement level of system-wide and a data use must match a system data use.  If the connector is
    orphaned (no system), skip the data use check. If conflicts, prefer the opt-out preference.
    """

    # OLD WORKFLOW
    if privacy_request.consent_preferences:
        return (
            all(
                consent_pref["opt_in"]
                for consent_pref in privacy_request.consent_preferences
            ),
            [],  # Don't need to return the filtered preferences, this is just relevant for the new workflow
        )

    # NEW WORKFLOW
    relevant_preferences = filter_privacy_preferences_for_propagation(
        system,
        privacy_request.privacy_preferences,  # type: ignore[attr-defined]
    )
    if not relevant_preferences:
        return None, []  # We should do nothing here

    # Collapse relevant preferences into whether we should opt-in or opt-out
    preference_to_propagate: UserConsentPreference = (
        UserConsentPreference.opt_out
        if any(
            filtered_pref.preference == UserConsentPreference.opt_out
            for filtered_pref in relevant_preferences
        )
        else UserConsentPreference.opt_in
    )

    # Hopefully rare final filtering in case there are conflicting preferences
    filtered_preferences: List[PrivacyPreferenceHistory] = [
        pref
        for pref in relevant_preferences
        if pref.preference == preference_to_propagate
    ]

    # Return whether we should opt in, and the filtered preferences so we can update those for consent reporting
    return preference_to_propagate == UserConsentPreference.opt_in, filtered_preferences


def cache_initial_status_and_identities_for_consent_reporting(
    db: Session,
    privacy_request: PrivacyRequest,
    connection_config: ConnectionConfig,
    relevant_preferences: List[PrivacyPreferenceHistory],
    relevant_user_identities: Dict[str, Any],
) -> None:
    """Add a pending system status and cache relevant identities on the applicable PrivacyPreferenceHistory
    records for consent reporting.

    Preferences that aren't relevant for the given system/connector are given a skipped status.

    Typically used when *some* but not all privacy preferences are relevant.  Otherwise,
    other methods just mark all the preferences as skipped.
    """
    for pref in privacy_request.privacy_preferences:  # type: ignore[attr-defined]
        if pref in relevant_preferences:
            pref.update_secondary_user_ids(db, relevant_user_identities)
            pref.cache_system_status(
                db, connection_config.system_key, ExecutionLogStatus.pending
            )
        else:
            pref.cache_system_status(
                db, connection_config.system_key, ExecutionLogStatus.skipped
            )


def add_complete_system_status_for_consent_reporting(
    db: Session,
    privacy_request: PrivacyRequest,
    connection_config: ConnectionConfig,
) -> None:
    """Cache a complete system status for consent reporting on just the subset
    of preferences that were deemed relevant for the connector on failure

    Deeming them relevant if they already had a "pending" log added to them.
    """
    for pref in privacy_request.privacy_preferences:  # type: ignore[attr-defined]
        if (
            pref.affected_system_status
            and pref.affected_system_status.get(connection_config.system_key)
            == ExecutionLogStatus.pending.value
        ):
            pref.cache_system_status(
                db,
                connection_config.system_key,
                ExecutionLogStatus.complete,
            )


def add_errored_system_status_for_consent_reporting(
    db: Session,
    privacy_request: PrivacyRequest,
    connection_config: ConnectionConfig,
) -> None:
    """Cache an errored system status for consent reporting on just the subset
    of preferences that were deemed relevant for the connector on failure

    Deeming them relevant if they already had a "pending" log added to them.
    """
    for pref in privacy_request.privacy_preferences:  # type: ignore[attr-defined]
        if (
            pref.affected_system_status
            and pref.affected_system_status.get(connection_config.system_key)
            == ExecutionLogStatus.pending.value
        ):
            pref.cache_system_status(
                db,
                connection_config.system_key,
                ExecutionLogStatus.error,
            )


def get_fides_user_device_id_provided_identity(
    db: Session, fides_user_device_id: Optional[str]
) -> Optional[ProvidedIdentity]:
    """Look up a fides user device id that is not attached to a privacy request if it exists

    There can be many fides user device ids attached to privacy requests, but we should try to keep them
    unique for consent requests.
    """
    if not fides_user_device_id:
        return None

    return ProvidedIdentity.filter(
        db=db,
        conditions=(
            (ProvidedIdentity.field_name == ProvidedIdentityType.fides_user_device_id)
            & (
                ProvidedIdentity.hashed_value
                == ProvidedIdentity.hash_value(fides_user_device_id)
            )
            & (ProvidedIdentity.privacy_request_id.is_(None))
        ),
    ).first()


def get_or_create_fides_user_device_id_provided_identity(
    db: Session,
    identity_data: Optional[Identity],
) -> ProvidedIdentity:
    """Gets an existing fides user device id provided identity or creates one if it doesn't exist.
    Raises an error if no fides user device id is supplied.
    """
    if not identity_data or not identity_data.fides_user_device_id:
        raise HTTPException(
            HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fides user device id not found in identity data",
        )

    identity = get_fides_user_device_id_provided_identity(
        db, identity_data.fides_user_device_id
    )

    if not identity:
        identity = ProvidedIdentity.create(
            db,
            data={
                "privacy_request_id": None,
                "field_name": ProvidedIdentityType.fides_user_device_id.value,
                "hashed_value": ProvidedIdentity.hash_value(
                    identity_data.fides_user_device_id
                ),
                "encrypted_value": {"value": identity_data.fides_user_device_id},
            },
        )

    return identity  # type: ignore[return-value]


def validate_notice_data_uses(
    privacy_notices: Iterable[Union[PrivacyNoticeWithId, PrivacyNoticeCreation]],
    db: Session,
) -> None:
    """
    Ensures that all the provided `PrivacyNotice`s data has valid data uses.
    Raises a 422 HTTP exception if an unknown data use is found on any `PrivacyNotice`
    """
    valid_data_uses = [data_use.fides_key for data_use in DataUse.query(db).all()]
    try:
        for privacy_notice in privacy_notices:
            privacy_notice.validate_data_uses(valid_data_uses)
    except ValueError as e:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


def ensure_unique_ids(
    privacy_notices: List[PrivacyNoticeWithId],
) -> None:
    """
    Ensures that all the provided `PrivacyNotice`s have unique IDs
    Raises a 422 HTTP exception if there is more than one PrivacyNotice with the same ID
    """
    ids = set()
    for privacy_notice in privacy_notices:
        if privacy_notice.id not in ids:
            ids.add(privacy_notice.id)
        else:
            raise HTTPException(
                HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"More than one provided PrivacyNotice with ID {privacy_notice.id}.",
            )


def create_privacy_notices_util(
    db: Session,
    privacy_notice_schemas: List[PrivacyNoticeCreation],
    should_escape: bool = True,
) -> Tuple[List[PrivacyNotice], Set[PrivacyNoticeRegion]]:
    """Performs validation before creating Privacy Notices and Privacy Notice History records
    and then ensures that Privacy Experiences exist for all Privacy Notices.
    """
    validate_notice_data_uses(privacy_notice_schemas, db)  # type: ignore[arg-type]

    existing_notices = PrivacyNotice.query(db).filter(PrivacyNotice.disabled.is_(False)).all()  # type: ignore[attr-defined]

    new_notices = [
        PrivacyNotice(**privacy_notice.dict(exclude_unset=True))
        for privacy_notice in privacy_notice_schemas
    ]
    check_conflicting_notice_keys(new_notices, existing_notices)
    for new_notice in new_notices:
        new_notice.validate_enabled_has_data_uses()

    created_privacy_notices: List[PrivacyNotice] = []
    affected_regions: Set = set()

    for privacy_notice in privacy_notice_schemas:
        if should_escape:
            # should_escape flag is for when we're creating a notice
            # from a template. The content was already escaped in the
            # template - we don't want to escape twice.
            privacy_notice = transform_fields(
                transformation=escape,
                model=privacy_notice,
                fields=PRIVACY_NOTICE_ESCAPE_FIELDS,
            )
        privacy_notice = transform_fields(
            transformation=jsonable_encoder,
            model=privacy_notice,
            fields=["gpp_field_mapping"],
        )
        created_privacy_notice = PrivacyNotice.create(
            db=db,
            data=privacy_notice.dict(exclude_unset=True),
            check_name=False,
        )
        created_privacy_notices.append(created_privacy_notice)
        affected_regions.update(created_privacy_notice.regions)

    # After creating any new notices, make sure experiences exist to back all notices.
    upsert_privacy_experiences_after_notice_update(
        db, affected_regions=list(affected_regions)
    )
    return created_privacy_notices, affected_regions


def validate_privacy_notice_dry_update(dry_update: PrivacyNotice) -> None:
    """
    Verify that a dry update of a PrivacyNotice satisfies the constraints
    for creating a privacy notice.

    This is done here instead of upfront because we need access to the current values
    of the privacy notice in the database combined with the patch updates from the request
    """
    try:
        PrivacyNoticeCreation.from_orm(dry_update)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            # pylint: disable=no-member
            detail=exc.errors(),  # type: ignore
        )


def prepare_privacy_notice_patches(
    privacy_notice_updates: List[PrivacyNoticeWithId],
    db: Session,
    model: Union[Type[PrivacyNotice], Type[PrivacyNoticeTemplate]],
) -> List[Tuple[PrivacyNoticeWithId, Optional[PRIVACY_NOTICE_TYPE]]]:
    """
    Prepares PrivacyNotice or Template upserts including performing data use
    conflict validation on proposed changes.

    For Privacy Notices, returns a list of tuples with the update data alongside the existing Privacy
    db record that will be updated.

    For PrivacyNoticeTemplates, returns a list of tuples with the data to be upserted, alongside
    the existing PrivacyNoticeTemplate if it exists or None otherwise.

    :param privacy_notice_updates: List of privacy notice schemas with ids: appropriate
    for editing PrivacyNotices or upserting PrivacyNoticeTemplates
    :param db: Session
    :param model: one of PrivacyNotice or PrivacyNoticeTemplate
    :return:
    """
    allow_create: bool = model == PrivacyNoticeTemplate
    ignore_disabled: bool = model != PrivacyNoticeTemplate

    # first we populate a map of privacy notices or templates in the db, indexed by ID
    existing_notices: Dict[str, PRIVACY_NOTICE_TYPE] = {}
    for existing_notice in model.query(db).all():
        existing_notices[existing_notice.id] = existing_notice

    # then associate existing notices/templates with their creates/updates
    # we'll return this set of data to actually process updates
    updates_and_existing: List[
        Tuple[PrivacyNoticeWithId, Optional[PRIVACY_NOTICE_TYPE]]
    ] = []
    for update_data in privacy_notice_updates:
        update_data = transform_fields(
            transformation=escape,
            model=update_data,
            fields=PRIVACY_NOTICE_ESCAPE_FIELDS,
        )
        update_data = transform_fields(
            transformation=jsonable_encoder,
            model=update_data,
            fields=["gpp_field_mapping"],
        )
        if update_data.id not in existing_notices:
            if not allow_create:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"No {model.__class__.__name__} found for id {update_data.id}.",
                )
            updates_and_existing.append((update_data, None))
        else:
            updates_and_existing.append((update_data, existing_notices[update_data.id]))

    # we temporarily store proposed update data in-memory for validation purposes only
    validation_updates: List[PRIVACY_NOTICE_TYPE] = []
    for update_data, existing_notice in updates_and_existing:
        # add the patched update to our temporary updates for validation
        if existing_notice:
            dry_update = existing_notice.dry_update(
                data=update_data.dict(exclude_unset=True)
            )
            validate_privacy_notice_dry_update(
                dry_update
            )  # Checks consent mechanism + delivery location
            validation_updates.append(
                existing_notice.dry_update(data=update_data.dict(exclude_unset=True))
            )
            # and don't include it anymore in the existing notices used for validation
            existing_notices.pop(existing_notice.id, None)
        else:
            # Add the pending created record to the the temporary updates for validation
            validation_updates.append(model(**update_data.dict(exclude_unset=True)))

    # run the validation here on our proposed "dry-run" updates
    try:
        check_conflicting_notice_keys(
            validation_updates,
            existing_notices.values(),
            ignore_disabled=ignore_disabled,
        )
        for validation_update in validation_updates:
            validation_update.validate_enabled_has_data_uses()

    except ValidationError as e:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)

    # return the tuples of update data associated with their existing db records
    return updates_and_existing


def upsert_privacy_notice_templates_util(
    db: Session,
    template_schemas: List[PrivacyNoticeWithId],
) -> List[PrivacyNoticeTemplate]:
    """
    Create or update *Privacy Notice Templates*. These are the resources that
    Fides ships with out of the box.
    """
    ensure_unique_ids(template_schemas)
    validate_notice_data_uses(template_schemas, db)

    upserts_and_existing: List[
        Tuple[PrivacyNoticeWithId, Optional[PrivacyNoticeTemplate]]
    ] = prepare_privacy_notice_patches(  # type: ignore[assignment]
        template_schemas,
        db,
        model=PrivacyNoticeTemplate,
    )

    upserted_templates = []
    for (
        create_or_update_data,
        existing_template,
    ) in upserts_and_existing:
        if existing_template:
            upserted_templates.append(
                existing_template.update(
                    db, data=create_or_update_data.dict(exclude_unset=True)
                )
            )
        else:
            upserted_templates.append(
                PrivacyNoticeTemplate.create(
                    db=db,
                    data=create_or_update_data.dict(exclude_unset=True),
                    check_name=False,
                )
            )
    return upserted_templates  # type: ignore[return-value]


def load_default_notices_on_startup(
    db: Session, notice_yaml_file_path: str
) -> Tuple[List[PrivacyNoticeTemplate], List[PrivacyNotice]]:
    """
    On startup, loads any new PrivacyNoticeTemplates into the database, and updates
    existing templates where applicable.

    Creates Privacy Notices from these templates, if no notices are linked to the given template
    already.  Otherwise, we skip making updates to the Notices themselves automatically.
    """
    logger.info(
        "Loading default privacy notice templates from {}", notice_yaml_file_path
    )
    with open(load_file([notice_yaml_file_path]), "r", encoding="utf-8") as file:
        notices = yaml.safe_load(file).get("privacy_notices", [])

        template_schemas: List[PrivacyNoticeWithId] = []

        # Validate templates
        for privacy_notice_data in notices:
            template_schemas.append(PrivacyNoticeWithId(**privacy_notice_data))

        # Upsert Privacy Notice Templates
        privacy_notice_templates: List[
            PrivacyNoticeTemplate
        ] = upsert_privacy_notice_templates_util(db, template_schemas)

        # Determine which templates don't have corresponding records in PrivacyNotice
        new_templates: List[PrivacyNoticeTemplate] = [
            template
            for template in privacy_notice_templates
            if template.id
            not in [origin for (origin,) in db.query(PrivacyNotice.origin).all()]
        ]

        # Link Privacy Notice Schemas to the Privacy Notice Templates
        notice_schemas: List[PrivacyNoticeCreation] = []
        for template in new_templates:
            privacy_notice_schema = PrivacyNoticeCreation.from_orm(template)
            privacy_notice_schema.origin = SafeStr(template.id)
            notice_schemas.append(privacy_notice_schema)

        # Create PrivacyNotice and PrivacyNoticeHistory records only for new templates
        # Not escaping here, because it was already escaped when the templates were created.
        new_privacy_notices, _ = create_privacy_notices_util(
            db, notice_schemas, should_escape=False
        )

        return new_templates, new_privacy_notices


def load_default_experience_configs_on_startup(
    db: Session, notice_yaml_file_path: str
) -> None:
    """
    On startup, loads default ExperienceConfigs into the database. Creates the defaults
    if they don't exist, otherwise, updates them with any new values from the default
    yaml file if applicable.
    """
    logger.info(
        "Loading default privacy experience configs from {}", notice_yaml_file_path
    )
    with open(load_file([notice_yaml_file_path]), "r", encoding="utf-8") as file:
        experience_configs = yaml.safe_load(file).get("privacy_experience_configs", [])

        for experience_config_data in experience_configs:
            create_default_experience_config(db, experience_config_data)


def create_default_experience_config(
    db: Session, experience_config_data: dict
) -> Optional[PrivacyExperienceConfig]:
    """Create a default experience config on startup.  The id is specified upfront.

    Split from load_default_experience_configs_on_startup for easier testing
    of a function that runs on application startup.
    """
    experience_config_data = (
        experience_config_data.copy()
    )  # Avoids unexpected behavior on update in testing

    experience_config_schema = transform_fields(
        transformation=escape,
        model=(ExperienceConfigCreateWithId(**experience_config_data)),
        fields=PRIVACY_EXPERIENCE_ESCAPE_FIELDS,
    )

    if not experience_config_schema.is_default:
        raise Exception("This method is for created default experience configs.")

    existing_experience_config = PrivacyExperienceConfig.get(
        db=db, object_id=experience_config_schema.id
    )

    if not existing_experience_config:
        logger.info(
            "Creating default experience config {}", experience_config_schema.id
        )
        return PrivacyExperienceConfig.create(
            db,
            data=experience_config_schema.dict(exclude_unset=True),
            check_name=False,
        )

    logger.info(
        "Found existing experience config {}, not creating a new default experience config",
        experience_config_schema.id,
    )
    return None


EEA_COUNTRIES: List[PrivacyNoticeRegion] = [
    PrivacyNoticeRegion.be,
    PrivacyNoticeRegion.bg,
    PrivacyNoticeRegion.cz,
    PrivacyNoticeRegion.dk,
    PrivacyNoticeRegion.de,
    PrivacyNoticeRegion.ee,
    PrivacyNoticeRegion.ie,
    PrivacyNoticeRegion.gr,
    PrivacyNoticeRegion.es,
    PrivacyNoticeRegion.fr,
    PrivacyNoticeRegion.hr,
    PrivacyNoticeRegion.it,
    PrivacyNoticeRegion.cy,
    PrivacyNoticeRegion.lv,
    PrivacyNoticeRegion.lt,
    PrivacyNoticeRegion.lu,
    PrivacyNoticeRegion.hu,
    PrivacyNoticeRegion.mt,
    PrivacyNoticeRegion.nl,
    PrivacyNoticeRegion.at,
    PrivacyNoticeRegion.pl,
    PrivacyNoticeRegion.pt,
    PrivacyNoticeRegion.ro,
    PrivacyNoticeRegion.si,
    PrivacyNoticeRegion.sk,
    PrivacyNoticeRegion.fi,
    PrivacyNoticeRegion.se,
    PrivacyNoticeRegion.gb_eng,
    PrivacyNoticeRegion.gb_sct,
    PrivacyNoticeRegion.gb_wls,
    PrivacyNoticeRegion.gb_nir,
    PrivacyNoticeRegion.no,
    PrivacyNoticeRegion["is"],
    PrivacyNoticeRegion.li,
    PrivacyNoticeRegion.eea,  # Catch-all region - can query this Experience directly to get a generic TCF experience
]


def create_tcf_experiences_on_startup(db: Session) -> List[PrivacyExperience]:
    """On startup, create TCF Overlay Experiences for all EEA Regions.  There
    are no Privacy Notices associated with these Experiences."""
    experiences_created: List[PrivacyExperience] = []
    for region in EEA_COUNTRIES:
        if not PrivacyExperience.get_experience_by_region_and_component(
            db,
            region.value,
            ComponentType.tcf_overlay,
        ):
            experiences_created.append(
                PrivacyExperience.create_default_experience_for_region(
                    db, region, ComponentType.tcf_overlay
                )
            )

    return experiences_created


def create_default_tcf_purpose_overrides_on_startup(
    db: Session,
) -> List[TCFPurposeOverride]:
    """On startup, load default Purpose Overrides, one for each purpose, with a default of is_included=True
    and no legal basis override

    The defaults have no effect on what is returned in the TCF Privacy Experience, and this functionality needs
    to be enabled via a config variable to be used at all.
    """
    purpose_override_resources_created: List[TCFPurposeOverride] = []

    for purpose_id in range(1, 12):
        if (
            not db.query(TCFPurposeOverride)
            .filter(TCFPurposeOverride.purpose == purpose_id)
            .first()
        ):
            purpose_override_resources_created.append(
                TCFPurposeOverride.create(
                    db, data={"purpose": purpose_id, "is_included": True}
                )
            )

    return purpose_override_resources_created
