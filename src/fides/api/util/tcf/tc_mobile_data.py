from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.privacy_experience import TCMobileData
from fides.api.util.tcf.tc_model import TCModel, build_tc_model
from fides.api.util.tcf.tc_string import (
    TCField,
    _get_max_vendor_id,
    get_bits_for_section,
)
from fides.api.util.tcf_util import TCFExperienceContents

CMP_SDK_ID = 1000000  # TODO pass in SDK ID
CMP_SDK_VERSION = 1


def build_tc_data_for_mobile(tcf_contents: TCFExperienceContents, consent_preference: UserConsentPreference) -> TCMobileData:
    """Build TC Data for Mobile App"""
    tc_model: TCModel = build_tc_model(tcf_contents, consent_preference)

    def build_binary_string(field_name: str, num_bits: int):
        return get_bits_for_section(
            [TCField(field_name=field_name, bits=num_bits)], tc_model
        )

    max_vendor_consents: int = _get_max_vendor_id(tc_model.vendor_consents)
    max_vendor_li: int = _get_max_vendor_id(tc_model.vendor_legitimate_interests)

    return TCMobileData(
        iab_tcf_cmp_sdk_id=CMP_SDK_ID,
        iab_tcf_cmp_sdk_version=CMP_SDK_VERSION,
        iab_tcf_policy_version=tc_model.policy_version,
        iab_tcf_gdpr_applies=1,  # TODO make this dynamic
        iab_tcf_publisher_cc=tc_model.publisher_country_code,
        iab_tcf_purpose_one_treatment=tc_model.purpose_one_treatment,
        iab_tcf_use_non_standard_texts=int(
            build_binary_string("use_non_standard_texts", 1)
        ),
        iab_tcf_vendor_consents=build_binary_string(
            "vendor_consents", max_vendor_consents
        ),
        iab_tcf_vendor_legitimate_interests=build_binary_string(
            "vendor_legitimate_interests", max_vendor_li
        ),
        iab_tcf_purpose_consents=build_binary_string("purpose_consents", 24),
        iab_tcf_purpose_legitimate_interests=build_binary_string(
            "purpose_legitimate_interests", 24
        ),
        iab_tcf_special_feature_opt_ins=build_binary_string(
            "special_feature_optins", 12
        ),
    )
