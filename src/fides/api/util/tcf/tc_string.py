import base64
from typing import Any, List, Optional

from pydantic import Field

from fides.api.schemas.base_class import FidesSchema
from fides.api.util.tcf.tc_model import TCModel


class TCField(FidesSchema):
    """Schema to represent a field within a TC string segment"""

    name: str = Field(description="Field name")
    bits: int = Field(
        description="The number of bits that should be used to represent this value"
    )
    value_override: Optional[Any] = Field(
        description="The value that should be used instead of a "
        "value of the same name on the TCModel"
    )


def get_bits_for_section(fields: List[TCField], tc_model: TCModel) -> str:
    """Construct a representation of the fields supplied in bits for a given section."""
    total_bits = ""
    for field in fields:
        field_value: Any = (
            field.value_override
            if field.value_override is not None
            else getattr(tc_model, field.name)
        )

        if isinstance(field_value, bool):
            field_value = 1 if field_value else 0

        bit_components = ""
        if isinstance(field_value, str):
            bit_allocation = int(field.bits / len(field_value))
            for char in field_value:
                converted_num = _convert_letter_to_number(char)
                bit_components += format(converted_num, f"0{bit_allocation}b")

        elif isinstance(field_value, list):
            for i in range(1, field.bits + 1):
                bit_components += "1" if i in field_value else "0"

        else:
            bit_components = format(field_value, f"0{field.bits}b")

        total_bits += bit_components
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
    Build the "core" TC String.
    """
    max_vendor_consents: int = _get_max_vendor_id(model.vendor_consents)
    max_vendor_li: int = _get_max_vendor_id(model.vendor_legitimate_interests)

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
        TCField(name="use_non_standard_texts", bits=1),
        TCField(name="special_feature_optins", bits=12),
        TCField(name="purpose_consents", bits=24),
        TCField(name="purpose_legitimate_interests", bits=24),
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
    """Build the Optional Disclosed Vendors" section of the TC String"""
    max_vendor_id: int = _get_max_vendor_id(model.vendors_disclosed)

    disclosed_vendor_fields: list = [
        TCField(name="segment_type", bits=3, value_override=1),
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
