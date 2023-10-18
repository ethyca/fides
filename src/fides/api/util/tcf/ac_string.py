from typing import List, Optional, Tuple

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


def build_ac_string(
    tcf_contents: TCFExperienceContents, preference: Optional[UserConsentPreference]
) -> Optional[str]:
    """Returns an AC string following this spec: https://support.google.com/admanager/answer/9681920"""
    if not tcf_contents.tcf_vendor_consents:
        # AC Vendors are automatically added to the Vendor Consents section if present
        return None

    if preference != UserConsentPreference.opt_in:
        # The AC string only encodes opt-ins!
        return None

    ac_vendors: List[int] = []
    for vendor in tcf_contents.tcf_vendor_consents:
        try:
            ac_vendors.append(universal_vendor_id_to_ac_id(vendor.id))
        except ValueError:
            continue

    if not ac_vendors:
        # No vendors found in AC format
        return None

    return (
        SPECIFICATION_VERSION_NUMBER
        + SEPARATOR_SYMBOL
        + ".".join([str(vendor_id) for vendor_id in sorted(ac_vendors)])
    )


def build_fides_string(tc_str: Optional[str], ac_str: Optional[str]) -> str:
    """Concatenate a TC string and an AC string into a 'fides string' representation"""
    if tc_str is None:
        tc_str = ""

    if not ac_str:
        return tc_str

    return f"{tc_str}{FIDES_SEPARATOR}{ac_str}"


def split_fides_string(fides_str: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Split a Fides String into separate TC Strings and AC Strings"""
    if not fides_str:
        return None, None

    split_str = fides_str.split(FIDES_SEPARATOR)
    tc_str = split_str[0] or None

    ac_str = None
    if len(split_str) > 1:
        ac_str = split_str[1]

    return tc_str, ac_str


def _ac_str_to_universal_vendor_id_list(ac_str: Optional[str]) -> List[str]:
    """Convert an AC string into a list of universal ac vendor ids"""
    if not ac_str:
        return []

    if not ac_str.startswith(SPECIFICATION_VERSION_NUMBER + SEPARATOR_SYMBOL):
        raise DecodeFidesStringError("Unexpected AC String format")

    ac_str = ac_str.lstrip(SPECIFICATION_VERSION_NUMBER).lstrip(SEPARATOR_SYMBOL)
    vendor_ids: List[str] = ac_str.split(".")
    universal_ac_vendor_ids: List[str] = []

    for vendor_id in vendor_ids:
        try:
            int(vendor_id)
        except ValueError:
            raise DecodeFidesStringError("Unexpected AC String format")
        universal_ac_vendor_ids.append(AC_PREFIX + vendor_id)

    return universal_ac_vendor_ids


def _convert_ac_strings_to_fides_preferences(
    current_ac_str: Optional[str],
    accept_all_ac_str: Optional[str],
) -> List[TCFVendorSave]:
    """Convert an AC string into a list of corresponding vendor preferences.

    Because AC strings only encode opt-ins, compare the passed in string with the AC string that would be
    built from the datamap if we opted into every AC vendor.  Vendors in both strings get an opt-in preference.
    AC vendors in the datamap but not in the string get an opt-out preference.
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
    """Method to convert an AC String into a FidesStringFidesPreferences object, which is a format from which
    its vendor_consent_preferences can be saved into the Fides database

    FE only shows consent toggle for AC vendors, so that's why we transform the AC String into that section.
    """
    if not ac_str:
        return FidesStringFidesPreferences()

    all_options_ac_string: Optional[str] = build_ac_string(
        tcf_contents, UserConsentPreference.opt_in
    )

    return FidesStringFidesPreferences(
        vendor_consent_preferences=_convert_ac_strings_to_fides_preferences(
            ac_str, all_options_ac_string
        ),
    )
