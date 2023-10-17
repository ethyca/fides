from typing import List, Optional

from fides.api.models.privacy_notice import UserConsentPreference
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
