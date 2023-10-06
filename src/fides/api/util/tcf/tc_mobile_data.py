import binascii
from typing import Dict, List, Optional

from iab_tcf import ConsentV2, decode_v2  # type: ignore[import]

from fides.api.common_exceptions import DecodeTCStringError
from fides.api.schemas.tcf import TCMobileData
from fides.api.util.tcf.tc_model import TCModel
from fides.api.util.tcf.tc_string import (
    PURPOSE_CONSENTS_BITS,
    PURPOSE_LEGITIMATE_INTERESTS_BITS,
    SPECIAL_FEATURE_BITS,
    USE_NON_STANDARD_TEXT_BITS,
    TCField,
    _get_max_vendor_id,
    build_tc_string,
    get_bits_for_section,
)


def build_tc_data_for_mobile(tc_model: TCModel) -> TCMobileData:
    """Build TC Data for Mobile App"""

    def _build_binary_string(name: str, num_bits: int) -> str:
        """Internal helper to build a bit string of 0's and 1's to represent list data
        pulled from the TC model using the prescribed number of bits"""
        return get_bits_for_section([TCField(name=name, bits=num_bits)], tc_model)

    # If vendors have consent or legitimate interest data, show the max id that exists.
    # This will end up being the bitstring length of these sections
    max_vendor_consents: int = _get_max_vendor_id(tc_model.vendor_consents)
    max_vendor_li: int = _get_max_vendor_id(tc_model.vendor_legitimate_interests)

    tc_string: str = build_tc_string(tc_model)

    return TCMobileData(
        IABTCF_CmpSdkID=tc_model.cmp_id,
        IABTCF_CmpSdkVersion=tc_model.cmp_version,
        IABTCF_PolicyVersion=tc_model.policy_version,
        IABTCF_gdprApplies=1,
        IABTCF_PublisherCC=tc_model.publisher_country_code,
        IABTCF_PurposeOneTreatment=tc_model.purpose_one_treatment,
        IABTCF_UseNonStandardTexts=int(
            _build_binary_string("use_non_standard_texts", USE_NON_STANDARD_TEXT_BITS)
        ),
        IABTCF_TCString=tc_string,
        IABTCF_VendorConsents=_build_binary_string(
            "vendor_consents", max_vendor_consents
        ),
        IABTCF_VendorLegitimateInterests=_build_binary_string(
            "vendor_legitimate_interests", max_vendor_li
        ),
        IABTCF_PurposeConsents=_build_binary_string(
            "purpose_consents", PURPOSE_CONSENTS_BITS
        ),
        IABTCF_PurposeLegitimateInterests=_build_binary_string(
            "purpose_legitimate_interests", PURPOSE_LEGITIMATE_INTERESTS_BITS
        ),
        IABTCF_SpecialFeaturesOptIns=_build_binary_string(
            "special_feature_optins", SPECIAL_FEATURE_BITS
        ),
    )


def _integer_dict_to_list(int_dict: Dict[int, bool]) -> List[int]:
    """Converts a dictionary of integers->booleans into a list of just the integers mapped to True"""
    return [identifier for identifier, consented in int_dict.items() if consented]


def convert_tc_string_to_mobile_data(tc_str: Optional[str]) -> Optional[TCMobileData]:
    """Helper to take a TC String if supplied and decode it into a TCMobileData format"""
    if not tc_str:
        return None

    try:
        decoded: ConsentV2 = decode_v2(tc_str)
    except binascii.Error:
        raise DecodeTCStringError("Invalid base64-encoded string")

    def _build_binary_string(
        name: str, num_bits: int, override: Optional[List[int]] = None
    ) -> str:
        """Internal helper to build a bit string of 0's and 1's to represent list data
        pulled from the Consent v2 model using the prescribed number of bits"""
        return get_bits_for_section(
            [TCField(name=name, bits=num_bits, value_override=override)], decoded
        )

    try:
        vendor_consents: List[int] = _integer_dict_to_list(decoded.consented_vendors)
        max_vendor_consents: int = _get_max_vendor_id(vendor_consents)

        vendor_legitimate_interests: List[int] = _integer_dict_to_list(
            decoded.interests_vendors
        )
        max_vendor_legitimate_interests: int = _get_max_vendor_id(
            vendor_legitimate_interests
        )

        return TCMobileData(
            IABTCF_CmpSdkID=decoded.cmp_id,
            IABTCF_CmpSdkVersion=decoded.cmp_version,
            IABTCF_PolicyVersion=decoded.tcf_policy_version,
            IABTCF_gdprApplies=1,
            IABTCF_PublisherCC=decoded.publisher_cc.decode(),
            IABTCF_PurposeOneTreatment=decoded.purpose_one_treatment,
            IABTCF_UseNonStandardTexts=int(
                _build_binary_string(
                    "use_non_standard_stacks", USE_NON_STANDARD_TEXT_BITS
                )
            ),
            IABTCF_TCString=tc_str,
            IABTCF_VendorConsents=_build_binary_string(
                "vendor_consents", max_vendor_consents, vendor_consents
            ),
            IABTCF_VendorLegitimateInterests=_build_binary_string(
                "vendor_legitimate_interests",
                max_vendor_legitimate_interests,
                vendor_legitimate_interests,
            ),
            IABTCF_PurposeConsents=_build_binary_string(
                "purpose_consents",
                PURPOSE_CONSENTS_BITS,
                _integer_dict_to_list(decoded.purposes_consent),
            ),
            IABTCF_PurposeLegitimateInterests=_build_binary_string(
                "purpose_legitimate_interests",
                PURPOSE_LEGITIMATE_INTERESTS_BITS,
                _integer_dict_to_list(decoded.purposes_legitimate_interests),
            ),
            IABTCF_SpecialFeaturesOptIns=_build_binary_string(
                "special_feature_optins",
                SPECIAL_FEATURE_BITS,
                _integer_dict_to_list(decoded.special_features_optin),
            ),
        )
    except AttributeError:
        raise DecodeTCStringError("Missing expected section(s) in TC String")
    except Exception as exc:
        raise DecodeTCStringError(f"Unexpected decode error encountered: {exc}")
