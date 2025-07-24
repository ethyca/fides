from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException
from sqlalchemy.orm import Query, Session
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_notice import (
    EnforcementLevel,
    PrivacyNotice,
    UserConsentPreference,
)
from fides.api.models.privacy_preference import PrivacyPreferenceHistory
from fides.api.models.privacy_request import (
    PrivacyRequest,
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.api.models.tcf_purpose_overrides import TCFPurposeOverride
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.redis_cache import Identity


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


def build_user_consent_and_filtered_preferences_for_service(
    system: Optional[System],
    privacy_request: PrivacyRequest,
    session: Session,
    is_notice_based: bool = False,
) -> Tuple[
    Optional[Union[bool, Dict[str, Dict[str, Any]]]],
    List[PrivacyPreferenceHistory],
]:
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

    # NEW WORKFLOWS: 1.notice-based and 2. global SaaS Consent
    relevant_preferences: List[PrivacyPreferenceHistory] = (
        filter_privacy_preferences_for_propagation(
            system,
            privacy_request.privacy_preferences,  # type: ignore[attr-defined]
        )
    )
    if not relevant_preferences:
        return None, []  # We should do nothing here

    filtered_preferences: List[PrivacyPreferenceHistory] = []

    # 1. NOTICE-BASED WORKFLOW
    if is_notice_based:
        notice_preference_map: Dict[str, Dict[str, Any]] = {}
        # retrieve notices from the DB if they are associated with a relevant preference
        notices_with_preference: Query = session.query(PrivacyNotice).filter(
            PrivacyNotice.notice_key.in_(
                [preference.notice_key for preference in relevant_preferences]
            ),
        )
        # build our notice id -> user preference map, build filtered list of preferences that apply
        for notice in notices_with_preference:
            preference = [
                pref
                for pref in relevant_preferences
                if pref.notice_key == notice.notice_key
            ]
            # we only expect max 1 preference in this list
            if preference and preference[0]:
                notice_preference_map[notice.id] = {
                    "preference": preference[0].preference,
                    "notice_key": notice.notice_key,
                }
                filtered_preferences.append(preference[0])

        return (
            notice_preference_map,
            filtered_preferences,
        )

    # 2. GLOBAL (OPT-IN/OUT) WORKFLOW
    preference_to_propagate: UserConsentPreference = (
        UserConsentPreference.opt_out
        if any(
            filtered_pref.preference == UserConsentPreference.opt_out
            for filtered_pref in relevant_preferences
        )
        else UserConsentPreference.opt_in
    )

    # Hopefully rare final filtering in case there are conflicting preferences
    filtered_preferences = [
        pref
        for pref in relevant_preferences
        if pref.preference == preference_to_propagate
    ]

    # Return whether we should opt in, and the filtered preferences so we can update those for consent reporting
    return (
        preference_to_propagate == UserConsentPreference.opt_in,
        filtered_preferences,
    )


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
    add_errored_system_status_for_consent_reporting_on_preferences(db, privacy_request.privacy_preferences, connection_config)  # type: ignore[attr-defined]


def add_errored_system_status_for_consent_reporting_on_preferences(
    db: Session,
    privacy_preferences: List[PrivacyPreferenceHistory],
    connection_config: ConnectionConfig,
) -> None:
    """
    Cache an errored system status for consent reporting on just the subset
    of preferences that were deemed relevant for the connector on failure,
    from the provided list of preferences.

    Deeming them relevant if they already had a "pending" log added to them.
    """
    for preference in privacy_preferences:
        if (
            preference.affected_system_status
            and preference.affected_system_status.get(connection_config.system_key)
            == ExecutionLogStatus.pending.value
        ):
            preference.cache_system_status(
                db,
                connection_config.system_key,  # type: ignore[arg-type]
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
            (
                ProvidedIdentity.field_name
                == ProvidedIdentityType.fides_user_device_id.value
            )
            & (
                ProvidedIdentity.hashed_value.in_(
                    ProvidedIdentity.hash_value_for_search(fides_user_device_id)
                )
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
