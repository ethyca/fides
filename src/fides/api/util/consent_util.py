from typing import Any, Dict, List, Optional, Tuple

import yaml
from fastapi import HTTPException
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.ctl.sql_models import System  # type: ignore[attr-defined]
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_experience import PrivacyExperienceConfig
from fides.api.models.privacy_notice import EnforcementLevel, UserConsentPreference
from fides.api.models.privacy_preference import PrivacyPreferenceHistory
from fides.api.models.privacy_request import (
    ExecutionLogStatus,
    PrivacyRequest,
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.schemas.privacy_experience import (
    ExperienceConfigCreate,
    ExperienceConfigCreateWithId,
    ExperienceConfigUpdate,
)
from fides.api.schemas.redis_cache import Identity


def filter_privacy_preferences_for_propagation(
    system: Optional[System], privacy_preferences: List[PrivacyPreferenceHistory]
) -> List[PrivacyPreferenceHistory]:
    """Filter privacy preferences on a privacy request to just the ones that should be considered for third party
    consent propagation"""

    propagatable_preferences: List[PrivacyPreferenceHistory] = [
        pref
        for pref in privacy_preferences
        if pref.privacy_notice_history.enforcement_level == EnforcementLevel.system_wide
        and pref.preference != UserConsentPreference.acknowledge
    ]

    if not system:
        return propagatable_preferences

    filtered_on_use: List[PrivacyPreferenceHistory] = []
    for pref in propagatable_preferences:
        if pref.privacy_notice_history.applies_to_system(system):
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
    identity_data: Identity,
) -> ProvidedIdentity:
    """Gets an existing fides user device id provided identity or creates one if it doesn't exist.
    Raises an error if no fides user device id is supplied.
    """
    if not identity_data.fides_user_device_id:
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
    with open(notice_yaml_file_path, "r", encoding="utf-8") as file:
        experience_configs = yaml.safe_load(file).get("privacy_experience_configs", [])

        for experience_config_data in experience_configs:
            upsert_default_experience_config(db, experience_config_data)


def upsert_default_experience_config(
    db: Session, experience_config_data: dict
) -> Tuple[bool, PrivacyExperienceConfig]:
    """Upserts an experience config - intended to be used for upserting default
    configs on startup.  The id is specified upfront.

    Returns whether the resource is new, and the experience config object.
    Split from load_default_experience_configs_on_startup for easier testing
    of a function that runs on application startup.
    """
    experience_config_data = (
        experience_config_data.copy()
    )  # Avoids unexpected behavior on update in testing

    experience_config_schema: ExperienceConfigCreateWithId = (
        ExperienceConfigCreateWithId(**experience_config_data)
    )
    if not experience_config_schema.is_default:
        raise Exception("This method is for created default experience configs.")

    existing_experience_config = PrivacyExperienceConfig.get(
        db=db, object_id=experience_config_schema.id
    )

    if existing_experience_config:
        logger.info(
            "Checking default experience config {} for updates",
            existing_experience_config.id,
        )

        dry_update: PrivacyExperienceConfig = existing_experience_config.dry_update(
            data=experience_config_schema.dict(exclude_unset=True)
        )
        # Validating some required fields if this is an overlay
        ExperienceConfigCreate.from_orm(dry_update)

        del experience_config_data["component"]
        del experience_config_data["id"]
        # This is important for making sure config is only updated if it actually changed
        update_data = ExperienceConfigUpdate(**experience_config_data)
        experience_config_data_dict: Dict = update_data.dict(exclude_unset=True)

        existing_experience_config.update(db=db, data=experience_config_data_dict)
        return False, existing_experience_config

    logger.info("Creating default experience config {}", experience_config_schema.id)
    new_experience_config = PrivacyExperienceConfig.create(
        db,
        data=experience_config_schema.dict(exclude_unset=True),
        check_name=False,
    )
    return True, new_experience_config
