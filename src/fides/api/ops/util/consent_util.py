from typing import List, Optional

from fides.api.ctl.sql_models import System  # type: ignore[attr-defined]
from fides.api.ops.schemas.privacy_request import PrivacyRequestConsentPreference


def _filter_matching_system_data_uses(
    system: System, preferences: List[PrivacyRequestConsentPreference]
) -> List[PrivacyRequestConsentPreference]:
    """Filter user's consent preferences to only ones that match data uses on the system

    Propagate preference if Privacy Notice Data Use and System Data Use match.
    Propagate preference if Privacy Notice Data Use is broader than System Data Use.
    Ignore preference if System Data Use is broader than Privacy Notice Data Use.
    """
    system_data_uses: List[str] = system.get_data_uses
    filtered_preferences: List[PrivacyRequestConsentPreference] = []

    for pref in preferences:
        privacy_notice_data_uses: List[str] = pref.privacy_notice_history.data_uses or []  # type: ignore[union-attr]
        for privacy_notice_data_use in privacy_notice_data_uses:
            for system_data_use in system_data_uses:
                if system_data_use.startswith(privacy_notice_data_use):
                    filtered_preferences.append(pref)

    return filtered_preferences


def filter_consent_preferences_for_propagation(
    system: Optional[System], consent_preferences: List[PrivacyRequestConsentPreference]
) -> List[PrivacyRequestConsentPreference]:
    """Filter consent preferences on a privacy request to just the ones that should be considered for third party
    consent propagation"""
    backwards_compatible_consent_requests: List[PrivacyRequestConsentPreference] = [
        pref for pref in consent_preferences if pref.data_use
    ]
    # Old workflow - Consent preferences saved with respect to data use.
    if backwards_compatible_consent_requests:
        return backwards_compatible_consent_requests

    # New workflow - Consent preferences saved with respect to privacy notices.
    system_wide_preferences: List[PrivacyRequestConsentPreference] = [
        pref
        for pref in consent_preferences
        if pref.privacy_notice_history
        and pref.privacy_notice_history.enforcement_level == "system_wide"
    ]

    if not system:
        return system_wide_preferences
    return _filter_matching_system_data_uses(system, system_wide_preferences)


def should_opt_in_to_service(
    system: Optional[System], consent_preferences: List[PrivacyRequestConsentPreference]
) -> Optional[bool]:
    """
    Given the user's consent preferences and an optional system, determine whether we should opt the user into the
    service, opt the user out, or do nothing.

    Filter consent preferences in a backwards compatible way so this both works with preferences saved with respect
    to a data use (old workflow) and new: consent preferences saved with respect to a privacy notice.

    If there are orphaned connectors, don't check System data uses.
    If conflicts, prefer the Opt-out preference.
    Enforcement level must be system_wide to propagate.
    """

    filtered_preferences = filter_consent_preferences_for_propagation(
        system, consent_preferences
    )
    if not filtered_preferences:
        return None  # We should do nothing here
    return all(filtered_pref.opt_in for filtered_pref in filtered_preferences)
