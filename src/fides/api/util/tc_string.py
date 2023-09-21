import base64
import json
import re
from datetime import datetime, timezone
from os.path import dirname, join
from typing import Union, List, Dict, Optional

from fides.api.schemas.tcf import TCFVendorRecord, TCFPurposeRecord, TCFFeatureRecord
from fides.config.helpers import load_file
from fideslang.models import LegalBasisForProcessingEnum
from pydantic import Field, NonNegativeInt, PositiveInt, validator, root_validator

from fides.api.models.privacy_experience import PrivacyExperience, ComponentType
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema

GVL_JSON_PATH = join(
    dirname(__file__),
    "../../../../clients/fides-js/src/lib/tcf",
    "gvl.json",
)


CMP_ID: int = 12  # TODO: hardcode our unique CMP ID after certification
CMP_VERSION = 1
CONSENT_SCREEN = 1  # TODO On which 'screen' consent was captured; this is a CMP proprietary number encoded into the TC string
FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS = [1, 3, 4, 5, 6]


class TCModel(FidesSchema):
    _gvl: Dict = {}

    isServiceSpecific: bool = Field(
        default=False,
        description="Whether the signals encoded in this TC String were from site-specific storage `true` versus "
        "‘global’ consensu.org shared storage `false`. A string intended to be stored in global/shared "
        "scope but the CMP is unable to store due to a user agent not accepting third-party cookies "
        "would be considered site-specific `true`.",
    )
    supportOOB: bool = Field(
        default=True,
        description="Whether or not this publisher supports OOB signaling.  On Global TC String OOB Vendors Disclosed "
        "will be included if the publish wishes to no allow these vendors they should set this to false.",
    )
    useNonStandardTexts: bool = Field(
        default=False,
        description="Non-standard stacks means that a CMP is using publisher-customized stack descriptions. Stacks "
        "(in terms of purposes in a stack) are pre-set by the IAB. As are titles. Descriptions are pre-set, "
        "but publishers can customize them. If they do, they need to set this bit to indicate that they've "
        "customized descriptions.",
    )
    purposeOneTreatment: bool = Field(
        default=False,
        description="`false` There is no special Purpose 1 status. Purpose 1 was disclosed normally (consent) as "
        "expected by Policy.  `true`Purpose 1 not disclosed at all. CMPs use PublisherCC to indicate the "
        "publisher’s country of establishment to help Vendors determine whether the vendor requires Purpose "
        "1 consent. In global scope TC strings, this field must always have a value of `false`. When a "
        "CMP encounters a global scope string with `purposeOneTreatment=true` then that string should be "
        "considered invalid and the CMP must re-establish transparency and consent.",
    )
    publisherCountryCode: str = "AA"
    version: int = 2
    consentScreen: PositiveInt = Field(
        default=1,
        description="The screen number is CMP and CmpVersion specific, and is for logging proof of consent. "
        "(For example, a CMP could keep records so that a publisher can request information about the "
        "context in which consent was gathered.)",
    )
    policyVersion: NonNegativeInt = Field(
        default=4,
        description="From the corresponding field in the GVL that was used for obtaining consent. A new policy version "
        "invalidates existing strings and requires CMPs to re-establish transparency and consent from users.",
    )
    consentLanguage: str = "EN"
    cmpId: NonNegativeInt = Field(
        default=0,
        description="A unique ID will be assigned to each Consent Manager Provider (CMP) from the iab.",
    )
    cmpVersion: PositiveInt = Field(
        default=1,
        description="Each change to an operating CMP should receive a new version number, for logging proof of "
        "consent. CmpVersion defined by each CMP.",
    )
    vendorListVersion: NonNegativeInt = Field(
        default=0,
        description="Version of the GVL used to create this TCModel. "
        "Global Vendor List versions will be released periodically.",
    )
    numCustomPurposes: int = 0

    created: int = None  # TODO make sure date is in the correct format
    lastUpdated: int = None  # TODO make sure date is in the correct format

    specialFeatureOptins: List = Field(
        default=[],
        description="The TCF designates certain Features as special, that is, a CMP must afford the user a means to "
        "opt in to their use. These Special Features are published and numbered in the GVL separately from "
        "normal Features. Provides for up to 12 special features.",
    )

    purposeConsents: List = Field(
        default=[],
        description="Renamed from `PurposesAllowed` in TCF v1.1. The user’s consent value for each Purpose established "
        "on the legal basis of consent. Purposes are published in the Global Vendor List (see. [[GVL]]).",
    )

    purposeLegitimateInterests: List = Field(
        default=[],
        description="The user’s permission for each Purpose established on the legal basis of legitimate interest. "
        "If the user has exercised right-to-object for a purpose.",
    )

    publisherConsents: List = Field(
        default=[],
        description="The user’s consent value for each Purpose established on the legal basis of consent, for the "
        "publisher.  Purposes are published in the Global Vendor List.",
    )

    publisherLegitimateInterests: List = Field(
        default=[],
        description="The user’s permission for each Purpose established on the legal basis of legitimate interest.  "
        "If the user has exercised right-to-object for a purpose.",
    )

    publisherCustomConsents: List = Field(
        default=[],
        description="The user’s consent value for each Purpose established on the legal basis of consent, for the "
        "publisher.  Purposes are published in the Global Vendor List.",
    )

    publisherCustomLegitimateInterests: List = Field(
        default=[],
        description="The user’s permission for each Purpose established on the legal basis of legitimate interest.  "
        "If the user has exercised right-to-object for a purpose that is established in the publisher's "
        "custom purposes.",
    )

    customPurposes: Dict = Field(
        default={},
        description="Set by a publisher if they wish to collect consent "
        "and LI Transparency for purposes outside of the TCF",
    )

    vendorConsents: List[int] = Field(
        default=[],
        description="Each [[Vendor]] is keyed by id. Their consent value is true if it is in the Vector",
    )

    vendorLegitimateInterests: List[int] = Field(
        default=[],
        description="Each [[Vendor]] is keyed by id. Whether their Legitimate Interests Disclosures have been "
        "established is stored as boolean.",
    )

    vendorsDisclosed: List = Field(
        default=[],
        description=" The value included for disclosed vendors signals which vendors have been disclosed to the user "
        "in the interface surfaced by the CMP. This section content is required when writing a TC string "
        "to the global (consensu) scope. When a CMP has read from and is updating a TC string from the "
        "global consensu.org storage, the CMP MUST retain the existing disclosure information and only"
        " add information for vendors that it has disclosed that had not been disclosed by other CMPs in "
        "prior interactions with this device/user agent.",
    )

    vendorsAllowed: List = Field(
        default=[],
        description="Signals which vendors the publisher permits to use OOB legal bases.",
    )

    publisherRestrictions: List = Field(
        default=[],
    )

    maxVendorConsent: Optional[int] = 0
    isVendorConsentRangeEncoding: int = 0
    maxVendorLI: Optional[int] = 0
    isVendorLIRangeEncoding: int = 0
    numPubRestrictions: int = 0

    @validator("publisherCountryCode")
    def check_publisher_country_code(cls, publisherCountryCode: str) -> str:
        """Validates that a publisherCountryCode is an upper-cased two letter string"""
        upper_case_country_code = publisherCountryCode.upper()
        """Validate the only one exercise action is provided"""
        pattern = r"^[A-Z]{2}$"
        if not re.match(pattern, upper_case_country_code):
            raise ValueError(
                "publisherCountryCode must be a length-2 string of alpha characters"
            )

        return upper_case_country_code

    @validator("consentLanguage")
    def check_consent_language(cls, consentLanguage: str) -> str:
        """Forces consent language to be upper cased and no longer than 2 characters"""
        return consentLanguage.upper()[:2]

    @validator("purposeLegitimateInterests")
    def filter_purpose_legitimate_interests(
        cls, purposeLegitimateInterests: List[int]
    ) -> List[int]:
        """Purpose 1 is never allowed to be true for legitimate interest As of TCF v2.2 purposes 3,4,5 & 6 are
        not allowed to be true for LI"""
        forbidden_l_i_legitimate_interests = [1, 3, 4, 5, 6]
        return [
            li
            for li in purposeLegitimateInterests
            if li not in forbidden_l_i_legitimate_interests
        ]

    @root_validator
    def temp_max_vendor_ids(cls, values: Dict) -> Dict:
        vendor_consents = values.get("vendorConsents")
        if vendor_consents:
            values["maxVendorConsent"] = max(
                [int(vendor_id) for vendor_id in vendor_consents]
            )

        vendor_li = values.get("vendorLegitimateInterests")
        if vendor_li:
            values["maxVendorLI"] = max([int(vendor_id) for vendor_id in vendor_li])

        return values


def transform_user_preference_to_boolean(preference: UserConsentPreference) -> bool:
    return preference in [
        UserConsentPreference.opt_in,
        UserConsentPreference.acknowledge,
    ]


def _build_vendor_consents_and_legitimate_interests(
    vendors: List[TCFVendorRecord], gvl_vendor_ids: List[str]
):
    vendor_consents: List[int] = []
    vendor_legitimate_interests: List[int] = []

    for vendor in vendors:
        if vendor.id not in gvl_vendor_ids:
            continue

        vendor_consents.append(int(vendor.id))

        leg_int_purpose_ids = [
            purpose
            for purpose in vendor.purposes
            if LegalBasisForProcessingEnum.LEGITIMATE_INTEREST.value
            in purpose.legal_bases
        ]

        # Ensure vendor doesn't have forbidden legint purpose set
        if not bool(
            set(leg_int_purpose_ids) & set(FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS)
        ):
            continue

        vendor_legitimate_interests.append(int(vendor.id))

    return vendor_consents, vendor_legitimate_interests


def _build_purpose_consent_and_legitimate_interests(purposes: List[TCFPurposeRecord]):
    purpose_consents: List[int] = []
    purpose_legitimate_interests: List[int] = []

    for purpose in purposes:
        if LegalBasisForProcessingEnum.CONSENT.value in purpose.legal_bases:
            purpose_consents.append(purpose.id)

        if (
            LegalBasisForProcessingEnum.LEGITIMATE_INTEREST.value in purpose.legal_bases
            and purpose.id not in FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS
        ):
            purpose_legitimate_interests.append(purpose.id)

    return purpose_consents, purpose_legitimate_interests


def _build_special_feature_opt_ins(special_features: List[TCFFeatureRecord]):
    special_feature_opt_ins: List[int] = []
    for special_feature in special_features:
        special_feature_opt_ins.append(special_feature.id)

    return special_feature_opt_ins


def build_tc_model(
    expanded_privacy_experience: PrivacyExperience, preference: UserConsentPreference
):
    """
    Helper for building a TC object for an accept-all or reject-all string
    """
    with open(load_file([GVL_JSON_PATH]), "r", encoding="utf-8") as file:
        gvl = json.load(file)

    internal_gvl_vendor_ids = list(gvl.get("vendors", {}).keys())

    # TODO not sure why adding this extra 0 to the epoch time is necessary for it to decode property
    # Matches this: Math.round(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), new Date().getUTCDate())/100)
    current_time = int(datetime.utcnow().date().strftime("%s") + "0")

    (
        vendor_consents,
        vendor_legitimate_interests,
    ) = _build_vendor_consents_and_legitimate_interests(
        expanded_privacy_experience.tcf_vendors, internal_gvl_vendor_ids
    )

    (
        purpose_consents,
        purpose_legitimate_interests,
    ) = _build_purpose_consent_and_legitimate_interests(
        expanded_privacy_experience.tcf_purposes
    )

    special_feature_opt_ins = _build_special_feature_opt_ins(
        expanded_privacy_experience.tcf_special_features
    )

    tc_model = TCModel(
        _gvl=gvl,
        cmpId=CMP_ID,
        vendorListVersion=gvl.get("vendorListVersion"),
        policyVersion=gvl.get("tcfPolicyVersion"),
        cmpVersion=CMP_VERSION,
        consentScreen=CONSENT_SCREEN,
        vendorsDisclosed=internal_gvl_vendor_ids,
        created=current_time,
        lastUpdated=current_time,
        vendorConsents=vendor_consents,
        vendorLegitimateInterests=vendor_legitimate_interests,
        purposeConsents=purpose_consents,
        purposeLegitimateInterests=purpose_legitimate_interests,  # TODO https://github.com/InteractiveAdvertisingBureau/iabtcf-es/blob/master/modules/core/src/encoder/SemanticPreEncoder.ts#L38
        specialFeatureOptins=special_feature_opt_ins,
    )

    consented: bool = transform_user_preference_to_boolean(preference)

    if not consented:
        # TODO Reject all path
        return

    return tc_model


def get_utc_now():
    return datetime.now(timezone.utc)


def build_tc_string(model):
    core_string = {
        "version": 6,
        "created": 36,
        "lastUpdated": 36,
        "cmpId": 12,
        "cmpVersion": 12,
        "consentScreen": 6,
        "consentLanguage": 12,
        "vendorListVersion": 12,
        "policyVersion": 6,
        "isServiceSpecific": 1,
        "useNonStandardTexts": 1,
        "specialFeatureOptins": 12,
        "purposeConsents": 24,
        "purposeLegitimateInterests": 24,
        "purposeOneTreatment": 1,
        "publisherCountryCode": 12,
        "maxVendorConsent": 16,
        "isVendorConsentRangeEncoding": 1,
        "vendorConsents": getattr(model, "maxVendorConsent"),
        "maxVendorLI": 16,
        "isVendorLIRangeEncoding": 1,
        "vendorLegitimateInterests": getattr(model, "maxVendorLI"),
        "numPubRestrictions": 12,
    }

    total_bits = ""
    for field, num_bits in core_string.items():
        val = getattr(model, field)

        if isinstance(val, bool):
            val = 1 if val else 0

        if field in ["consentLanguage", "publisherCountryCode"]:
            first_letter = ord(val[0]) - ord("A")
            second_letter = ord(val[1]) - ord("A")

            first_bit_components = format(first_letter, f"0{6}b")
            second_bit_components = format(second_letter, f"0{6}b")
            bit_components = first_bit_components + second_bit_components

        elif isinstance(val, list):
            bit_components = ""
            for i in range(1, num_bits + 1):
                bit_components += "1" if i in val else "0"

        else:
            bit_components = format(val, f"0{num_bits}b")

        total_bits += bit_components

    return base64.urlsafe_b64encode(bitstring_to_bytes(total_bits))


def bitstring_to_bytes(s):
    """Add the 0's at the end"""
    while len(s) % 8 != 0:
        s += "0"

    integer_val = int(s, 2)
    return integer_val.to_bytes((len(s) + 7) // 8, byteorder="big")
