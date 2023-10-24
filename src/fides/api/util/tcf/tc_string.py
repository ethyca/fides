import base64
import binascii
from typing import Any, Dict, List, Optional, Type, Union

from iab_tcf import ConsentV2, decode_v2  # type: ignore[import]
from pydantic import Field

from fides.api.common_exceptions import DecodeFidesStringError
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_preference import FidesStringFidesPreferences
from fides.api.schemas.tcf import TCFPurposeSave, TCFSpecialFeatureSave, TCFVendorSave
from fides.api.util.tcf.tc_model import TCModel, convert_tcf_contents_to_tc_model

# Number of bits allowed for certain sections that are used in multiple places
from fides.api.util.tcf.tcf_experience_contents import GVL_PREFIX, TCFExperienceContents

USE_NON_STANDARD_TEXT_BITS = 1
SPECIAL_FEATURE_BITS = 12
PURPOSE_CONSENTS_BITS = 24
PURPOSE_LEGITIMATE_INTERESTS_BITS = 24


def add_gvl_prefix(vendor_id: str) -> str:
    """Add gvl prefix to create a universal gvl identifier for the given vendor id"""
    return GVL_PREFIX + vendor_id


class TCField(FidesSchema):
    """Schema to represent a field within a TC string segment"""

    name: str = Field(description="Field name")
    bits: int = Field(
        description="The number of bits that should be used to represent this value"
    )
    value_override: Optional[Any] = Field(
        description="The value that should be used instead of the field on the TC model"
    )


def get_bits_for_section(fields: List[TCField], tc_model: TCModel) -> str:
    """Construct a representation of the fields supplied in bits for a given section."""

    def _convert_val_to_bitstring(val: Union[str, list, int], num_bits: int) -> str:
        """Internal helper to take a string, list of integers, or integer, and convert it to a bitstring"""
        bit_components: str = ""

        if isinstance(val, str):
            # Used for things like publisher country code and consent_language.
            # There are two letters, represented by 12 bits total, so we convert
            # the letters to numbers, and they are represented by 6 bits apiece
            bit_allocation = int(num_bits / len(val))
            for char in val:
                converted_num: int = _convert_letter_to_number(char)
                bit_components += format(converted_num, f"0{bit_allocation}b")
            return bit_components

        if isinstance(val, list):
            # List of integers expected.  Bitstring should be the length of the
            # maximum integer in the list
            for i in range(1, num_bits + 1):
                bit_components += "1" if i in val else "0"
            return bit_components

        # Converts an integer to bits, padding to use the specified number of bits
        return format(val, f"0{num_bits}b")

    total_bits: str = ""
    for field in fields:
        # Either fetch the field of the same name off of the TCModel for encoding,
        # or use the value override, if supplied.
        field_value: Any = (
            field.value_override
            if field.value_override is not None
            else getattr(tc_model, field.name)
        )

        # Cleanup before building bit strings by converting bools to ints
        if isinstance(field_value, bool):
            field_value = int(field_value)

        # Converting field value to bitstring of specified length and add that onto the string we're building
        total_bits += _convert_val_to_bitstring(field_value, field.bits)
    return total_bits


def _convert_letter_to_number(letter: str) -> int:
    """A->0, Z->25"""
    return ord(letter) - ord("A")


def _convert_bitstring_to_bytes(bitstr: str) -> bytes:
    """Convert a string of 0's and 1's to bytes, padded to both work with base64
    and bit->byte conversion"""
    least_common_multiple = 24  # 6 bits (basis for base 64) and 8 bits (one byte)
    padding: int = len(bitstr) % least_common_multiple
    new_bits: str = "0" * (least_common_multiple - padding)
    bitstr += new_bits

    integer_val: int = int(bitstr, 2)
    return integer_val.to_bytes((len(bitstr)) // 8, byteorder="big")


def _get_max_vendor_id(vendor_list: List[int]) -> int:
    """Get the maximum vendor id in the supplied list"""
    if not vendor_list:
        return 0

    return max(int(vendor_id) for vendor_id in vendor_list)


def build_tc_string(model: TCModel) -> str:
    """Construct a TC String from the given TCModel

    Currently only core and vendors_disclosed sections are supported.
    """
    core_string: str = build_core_string(model)
    vendors_disclosed_string: str = build_disclosed_vendors_string(model)

    return core_string + "." + vendors_disclosed_string


def build_core_string(model: TCModel) -> str:
    """
    Build the "core" TC String

    https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework/blob/master/TCFv2/IAB%20Tech%20Lab%20-%20Consent%20string%20and%20vendor%20list%20formats%20v2.md#the-core-string
    """
    max_vendor_consents: int = _get_max_vendor_id(model.vendor_consents)
    max_vendor_li: int = _get_max_vendor_id(model.vendor_legitimate_interests)

    # List of core fields.  Order is intentional!
    core_fields: list = [
        TCField(name="version", bits=6),
        TCField(name="created", bits=36),
        TCField(name="last_updated", bits=36),
        TCField(name="cmp_id", bits=12),
        TCField(name="cmp_version", bits=12),
        TCField(name="consent_screen", bits=6),
        TCField(name="consent_language", bits=12),
        TCField(name="vendor_list_version", bits=12),
        TCField(name="policy_version", bits=6),
        TCField(name="is_service_specific", bits=1),
        TCField(name="use_non_standard_texts", bits=USE_NON_STANDARD_TEXT_BITS),
        TCField(name="special_feature_optins", bits=SPECIAL_FEATURE_BITS),
        TCField(name="purpose_consents", bits=PURPOSE_CONSENTS_BITS),
        TCField(
            name="purpose_legitimate_interests", bits=PURPOSE_LEGITIMATE_INTERESTS_BITS
        ),
        TCField(name="purpose_one_treatment", bits=1),
        TCField(name="publisher_country_code", bits=12),
        TCField(name="max_vendor_consent", bits=16, value_override=max_vendor_consents),
        TCField(
            name="is_vendor_consent_range_encoding", bits=1, value_override=0
        ),  # Using bitfield
        TCField(name="vendor_consents", bits=max_vendor_consents),
        TCField(name="max_vendor_li", bits=16, value_override=max_vendor_li),
        TCField(
            name="is_vendor_li_range_encoding", bits=1, value_override=0
        ),  # Using bitfield
        TCField(name="vendor_legitimate_interests", bits=max_vendor_li),
        TCField(name="num_pub_restrictions", bits=12),
    ]

    core_bits: str = get_bits_for_section(core_fields, model)
    return base64.urlsafe_b64encode(_convert_bitstring_to_bytes(core_bits)).decode()


def build_disclosed_vendors_string(model: TCModel) -> str:
    """Build the Optional Disclosed Vendors" section of the TC String

    https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework/blob/master/TCFv2/IAB%20Tech%20Lab%20-%20Consent%20string%20and%20vendor%20list%20formats%20v2.md#disclosed-vendors
    """
    max_vendor_id: int = _get_max_vendor_id(model.vendors_disclosed)

    # List of disclosed vendor fields.  Order is intentional!
    disclosed_vendor_fields: list = [
        TCField(
            name="segment_type", bits=3, value_override=1
        ),  # 1 for Disclosed Vendors section
        TCField(name="max_vendor_id", bits=16, value_override=max_vendor_id),
        TCField(
            name="is_range_encoding", bits=1, value_override=0
        ),  # Using Bitfield encoding
        TCField(
            name="vendors_disclosed",
            bits=max_vendor_id,
            value_override=model.vendors_disclosed,
        ),
    ]

    disclosed_vendor_bits: str = get_bits_for_section(disclosed_vendor_fields, model)
    return base64.urlsafe_b64encode(
        _convert_bitstring_to_bytes(disclosed_vendor_bits)
    ).decode()


def boolean_to_user_consent_preference(preference: bool) -> UserConsentPreference:
    return UserConsentPreference.opt_in if preference else UserConsentPreference.opt_out


FidesPreferenceType = Union[TCFPurposeSave, TCFVendorSave, TCFSpecialFeatureSave]


def convert_to_fides_preference(
    datamap_options: List[int],
    tc_string_preferences: Dict[int, bool],
    preference_class: Union[
        Type[TCFPurposeSave], Type[TCFVendorSave], Type[TCFSpecialFeatureSave]
    ],
) -> List[FidesPreferenceType]:
    """For a field in the TC string, convert to a list of preferences where we opt-in if it is included in the string,
    and opt-out if it is not in the string, but in the datamap"""
    # Loop through all the datamap options that are currently available.  For example, all of the vendors
    # from the datamap against which we can save preferences with a consent legal basis
    preferences_array: List[FidesPreferenceType] = []

    for identifier in datamap_options:
        # Check if there's an opt_in encoded in the string.  Otherwise, we assume the user is opting out.
        preference: bool = tc_string_preferences.get(identifier, False)

        if preference_class == TCFVendorSave:
            # Vendors are currently saved as strings in our db.
            # We also need to add the gvl prefix here to turn this into
            # a universal vendor id.
            vendor_id: str = add_gvl_prefix(str(identifier))
            fides_preference: FidesPreferenceType = preference_class(
                id=vendor_id, preference=boolean_to_user_consent_preference(preference)
            )
        else:
            fides_preference = preference_class(
                id=identifier, preference=boolean_to_user_consent_preference(preference)
            )

        preferences_array.append(fides_preference)
    return preferences_array


def decode_tc_string_to_preferences(
    tc_string: Optional[str], tcf_contents: TCFExperienceContents
) -> FidesStringFidesPreferences:
    """Method to convert a TC String into a TCStringFidesPreferences object, which is a format from which
    preferences can be saved into the Fides database"""
    if not tc_string:
        return FidesStringFidesPreferences()
    try:
        # Decode the string and pull the user opt-ins off of the string
        decoded: ConsentV2 = decode_v2(tc_string)
        tc_str_p_c: Dict[int, bool] = decoded.purposes_consent
        tc_str_p_li: Dict[int, bool] = decoded.purposes_legitimate_interests
        tc_str_v_c: Dict[int, bool] = decoded.consented_vendors
        tc_str_v_li: Dict[int, bool] = decoded.interests_vendors
        tc_str_sf: Dict[int, bool] = decoded.special_features_optin
    except (binascii.Error, AttributeError):
        raise DecodeFidesStringError("Invalid base64-encoded TC string")

    # From our datamap, build all the possible options for the TC string, if the user
    # opted into everything
    all_options_tc_model: TCModel = convert_tcf_contents_to_tc_model(
        tcf_contents, UserConsentPreference.opt_in
    )
    datamap_p_c: List[int] = all_options_tc_model.purpose_consents
    datamap_p_li: List[int] = all_options_tc_model.purpose_legitimate_interests
    datamap_v_c: List[int] = all_options_tc_model.vendor_consents
    datamap_v_li: List[int] = all_options_tc_model.vendor_legitimate_interests
    datamap_sf: List[int] = all_options_tc_model.special_feature_optins

    # Return TCString Preferences that are driven by the datamap.  For every element in the datamap,
    # consider it an opt-in preference if it's included in the TC string, otherwise, consider
    # it an opt-out preference.
    return FidesStringFidesPreferences(
        purpose_consent_preferences=convert_to_fides_preference(
            datamap_p_c, tc_str_p_c, TCFPurposeSave
        ),
        purpose_legitimate_interests_preferences=convert_to_fides_preference(
            datamap_p_li, tc_str_p_li, TCFPurposeSave
        ),
        vendor_consent_preferences=convert_to_fides_preference(
            datamap_v_c, tc_str_v_c, TCFVendorSave
        ),
        vendor_legitimate_interests_preferences=convert_to_fides_preference(
            datamap_v_li, tc_str_v_li, TCFVendorSave
        ),
        special_feature_preferences=convert_to_fides_preference(
            datamap_sf, tc_str_sf, TCFSpecialFeatureSave
        ),
    )
