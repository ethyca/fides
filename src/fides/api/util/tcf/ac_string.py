from typing import List, Optional

from fides.api.common_exceptions import DecodeFidesStringError
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.privacy_preference import FidesStringFidesPreferences
from fides.api.schemas.tcf import TCFVendorSave
from fides.api.util.tcf.tcf_experience_contents import AC_PREFIX, TCFExperienceContents

SPECIFICATION_VERSION_NUMBER = "1"
SEPARATOR_SYMBOL = "~"
FIDES_SEPARATOR = ","


def universal_vendor_id_to_ac_id(universal_vendor_id: str) -> int:
    """Converts a universal ac vendor id to a vendor id

    For example, converts "gacp.42" to integer 42. Throws a ValueError if this
    is not an AC id.

    """
    if not universal_vendor_id.startswith(AC_PREFIX):
        raise ValueError

    return int(universal_vendor_id.partition(AC_PREFIX)[2])


def build_ac_vendor_consents(
    tcf_contents: TCFExperienceContents, preference: Optional[UserConsentPreference]
) -> List[int]:
    """Build a list of integers representing AC vendors with opt-in consent

    This is a prerequisite step for building an accept-all AC string powered by our datamap.  If
    a reject-all string is being built, we just return an empty list here.
    """
    if preference != UserConsentPreference.opt_in:
        # The AC string only encodes opt-ins, so we exit early here.
        return []

    ac_vendors: List[int] = []
    for vendor in tcf_contents.tcf_vendor_consents or []:
        #  AC vendors are surfaced in the`tcf_vendor_consents` section of the TCF Experience
        try:
            ac_vendors.append(universal_vendor_id_to_ac_id(vendor.id))
        except ValueError:
            continue
    return ac_vendors


def build_ac_string(ac_vendor_consents: List[int]) -> Optional[str]:
    """Returns an AC string following this spec: https://support.google.com/admanager/answer/9681920"""
    return (
        SPECIFICATION_VERSION_NUMBER
        + SEPARATOR_SYMBOL
        + ".".join([str(vendor_id) for vendor_id in sorted(ac_vendor_consents)])
    )


def validate_ac_string_format(ac_str: Optional[str]) -> None:
    """Run some preliminary validation checks on the AC str"""
    if not ac_str:
        return

    if not ac_str.startswith(SPECIFICATION_VERSION_NUMBER + SEPARATOR_SYMBOL):
        raise DecodeFidesStringError("Unexpected AC String format")

    ac_str = ac_str.lstrip(SPECIFICATION_VERSION_NUMBER).lstrip(SEPARATOR_SYMBOL)

    if not ac_str:
        # Return if AC string was just this format "1~"
        return

    try:
        [int(vendor_id) for vendor_id in ac_str.split(".")]
    except ValueError:
        raise DecodeFidesStringError("Unexpected AC String format")


def _ac_str_to_universal_vendor_id_list(ac_str: Optional[str]) -> List[str]:
    """Helper to convert an AC string into a list of universal ac vendor ids

    Used when saving preferences from an AC string
    """
    if not ac_str:
        return []

    validate_ac_string_format(ac_str)

    ac_str = ac_str.lstrip(SPECIFICATION_VERSION_NUMBER).lstrip(SEPARATOR_SYMBOL)

    if not ac_str:
        return []

    vendor_ids: List[str] = ac_str.split(".")

    universal_ac_vendor_ids: List[str] = [
        AC_PREFIX + vendor_id for vendor_id in vendor_ids
    ]

    return universal_ac_vendor_ids


def _convert_ac_strings_to_fides_preferences(
    current_ac_str: Optional[str],
    accept_all_ac_str: Optional[str],
) -> List[TCFVendorSave]:
    """Helper to convert an AC string into a list of corresponding vendor preferences, for saving preferences
    from an AC string.

    AC strings only encode opt-ins, so by itself, this doesn't give us explicit opt-outs. We compare the passed-in AC
    String with the accept-all AC string built at runtime against our current datamap.

    Vendors in both strings are saved as an opt-in.  AC vendors in the datamap, but not in the supplied AC string,
    get persisted as an explicit opt-out.
    """
    ac_string_vendor_ids: List[str] = _ac_str_to_universal_vendor_id_list(
        current_ac_str
    )
    accept_all_ac_vendor_ids: List[str] = _ac_str_to_universal_vendor_id_list(
        accept_all_ac_str
    )

    preferences_array: List[TCFVendorSave] = []

    for datamap_vendor_id in accept_all_ac_vendor_ids:
        preferences_array.append(
            TCFVendorSave(
                id=datamap_vendor_id,
                preference=UserConsentPreference.opt_in
                if datamap_vendor_id in ac_string_vendor_ids
                else UserConsentPreference.opt_out,
            )
        )

    return preferences_array


def decode_ac_string_to_preferences(
    ac_str: Optional[str], tcf_contents: TCFExperienceContents
) -> FidesStringFidesPreferences:
    """Method to convert a passed-in AC String into a FidesStringFidesPreferences object, which is a format from which
    its vendor_consent_preferences can be saved into the Fides database

    We will save vendors in the AC string as "vendor consents" because the FE only shows consent toggles for
    AC vendors by default.
    """
    if not ac_str:
        return FidesStringFidesPreferences()

    # Build an AC string from the datamap that would assume the user opted into all, as a comparison
    ac_vendor_consents: List[int] = build_ac_vendor_consents(
        tcf_contents, UserConsentPreference.opt_in
    )
    all_options_ac_string: Optional[str] = build_ac_string(ac_vendor_consents)

    return FidesStringFidesPreferences(
        vendor_consent_preferences=_convert_ac_strings_to_fides_preferences(
            ac_str, all_options_ac_string
        ),
    )
