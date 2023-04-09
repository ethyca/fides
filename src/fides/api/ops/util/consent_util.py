from typing import List, Optional

from fides.api.ctl.sql_models import System  # type: ignore[attr-defined]
from fides.api.ops.models.privacy_notice import EnforcementLevel
from fides.api.ops.models.privacy_preference import (
    PrivacyPreferenceHistory,
    UserConsentPreference,
)
from fides.api.ops.models.privacy_request import PrivacyRequest


def _filter_matching_system_data_uses(
    system: System, preferences: List[PrivacyPreferenceHistory]
) -> List[PrivacyPreferenceHistory]:
    """Filter user's privacy preferences to only ones that match data uses on the system.

    Propagate preference if Privacy Notice Data Use and System Data Use match or the Privacy Notice
    Data Use is a parent of a System Data Use.
    """
    filtered_preferences: List[PrivacyPreferenceHistory] = []
    for pref in preferences:
        privacy_notice_data_uses: List[str] = pref.privacy_notice_history.data_uses or []  # type: ignore[union-attr]
        for privacy_notice_data_use in privacy_notice_data_uses:
            for system_data_use in system.get_data_uses(include_parents=True):
                if system_data_use == privacy_notice_data_use:
                    filtered_preferences.append(pref)

    return filtered_preferences


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
    return _filter_matching_system_data_uses(system, propagatable_preferences)


def should_opt_in_to_service(
    system: Optional[System], privacy_request: PrivacyRequest
) -> Optional[bool]:
    """
    Determine if we should opt in (return True), opt out (return False), or do nothing (return None) for the given System.

    - If using the old workflow (privacyrequest.consent_preferences), return True if all attached consent preferences
    are opt in, otherwise False.  System check is ignored.

    - If using the new workflow (privacyrequest.privacy_preferences), there is more filtering here.  Privacy Preferences
    must have an enforcement level of system-wide and a data use must match a system data use.  If the connector is
    orphaned (no system), skip the data use check. If conflicts, prefer the opt-out preference.
    """

    # OLD WORKFLOW
    if privacy_request.consent_preferences:
        return all(
            consent_pref["opt_in"]
            for consent_pref in privacy_request.consent_preferences
        )

    # NEW WORKFLOW
    filtered_preferences = filter_privacy_preferences_for_propagation(
        system, privacy_request.privacy_preferences
    )
    if not filtered_preferences:
        return None  # We should do nothing here

    return all(
        filtered_pref.preference == UserConsentPreference.opt_in
        for filtered_pref in filtered_preferences
    )
