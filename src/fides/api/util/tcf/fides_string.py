from typing import Optional, Tuple

from fides.api.common_exceptions import DecodeFidesStringError
from fides.api.util.tcf.ac_string import FIDES_SEPARATOR, validate_ac_string_format


def build_fides_string(tc_str: Optional[str], ac_str: Optional[str]) -> str:
    """Concatenate a TC string and an AC string into a 'fides string' representation, to represent
    both in a single string"""
    if not tc_str:
        raise DecodeFidesStringError("TC String is required for a complete signal")

    if not ac_str:
        return tc_str

    return f"{tc_str}{FIDES_SEPARATOR}{ac_str}"


def split_fides_string(fides_str: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Split a Fides String into separate TC Strings and AC Strings

    Run some upfront validation here on the Fides String format as a whole, and the AC string section.
    TC string section validation is more complex and happens elsewhere.
    """
    if not fides_str:
        return None, None

    split_str = fides_str.split(FIDES_SEPARATOR)
    tc_str = split_str[0]
    if not tc_str:
        raise DecodeFidesStringError("TC String is required for a complete signal")

    ac_str: Optional[str] = split_str[1] if len(split_str) > 1 else None

    validate_ac_string_format(ac_str)
    return tc_str, ac_str
