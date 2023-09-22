import hashlib
import json
import re
from datetime import datetime
from os.path import dirname, join
from typing import Dict, List, Optional, Tuple

from fideslang.models import LegalBasisForProcessingEnum
from pydantic import (
    Extra,
    Field,
    NonNegativeInt,
    PositiveInt,
    root_validator,
    validator,
)

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.tcf import TCFFeatureRecord, TCFPurposeRecord, TCFVendorRecord
from fides.api.util.tcf_util import TCFExperienceContents
from fides.config.helpers import load_file

GVL_JSON_PATH = join(
    dirname(__file__),
    "../../../../../clients/fides-js/src/lib/tcf",
    "gvl.json",
)


CMP_ID: int = 12  # TODO: hardcode our unique CMP ID after certification
CMP_VERSION = 1
CONSENT_SCREEN = 1  # TODO On which 'screen' consent was captured; this is a CMP proprietary number encoded into the TC string
FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS = [1, 3, 4, 5, 6]


class TCModel(FidesSchema):
    _gvl: Dict = {}

    is_service_specific: bool = Field(
        default=False,
        description="Whether the signals encoded in this TC String were from site-specific storage `true` versus "
        "‘global’ consensu.org shared storage `false`. A string intended to be stored in global/shared "
        "scope but the CMP is unable to store due to a user agent not accepting third-party cookies "
        "would be considered site-specific `true`.",
    )
    support_oob: bool = Field(
        default=True,
        description="Whether or not this publisher supports OOB signaling.  On Global TC String OOB Vendors Disclosed "
        "will be included if the publish wishes to no allow these vendors they should set this to false.",
    )
    use_non_standard_texts: bool = Field(
        default=False,
        description="Non-standard stacks means that a CMP is using publisher-customized stack descriptions. Stacks "
        "(in terms of purposes in a stack) are pre-set by the IAB. As are titles. Descriptions are pre-set, "
        "but publishers can customize them. If they do, they need to set this bit to indicate that they've "
        "customized descriptions.",
    )
    purpose_one_treatment: bool = Field(
        default=False,
        description="`false` There is no special Purpose 1 status. Purpose 1 was disclosed normally (consent) as "
        "expected by Policy.  `true`Purpose 1 not disclosed at all. CMPs use PublisherCC to indicate the "
        "publisher’s country of establishment to help Vendors determine whether the vendor requires Purpose "
        "1 consent. In global scope TC strings, this field must always have a value of `false`. When a "
        "CMP encounters a global scope string with `purposeOneTreatment=true` then that string should be "
        "considered invalid and the CMP must re-establish transparency and consent.",
    )
    publisher_country_code: str = "AA"
    version: int = 2
    consent_screen: PositiveInt = Field(
        default=1,
        description="The screen number is CMP and CmpVersion specific, and is for logging proof of consent. "
        "(For example, a CMP could keep records so that a publisher can request information about the "
        "context in which consent was gathered.)",
    )
    policy_version: NonNegativeInt = Field(
        default=4,
        description="From the corresponding field in the GVL that was used for obtaining consent. A new policy version "
        "invalidates existing strings and requires CMPs to re-establish transparency and consent from users.",
    )
    consent_language: str = "EN"
    cmp_id: NonNegativeInt = Field(
        default=0,
        description="A unique ID will be assigned to each Consent Manager Provider (CMP) from the iab.",
    )
    cmp_version: PositiveInt = Field(
        default=1,
        description="Each change to an operating CMP should receive a new version number, for logging proof of "
        "consent. CmpVersion defined by each CMP.",
    )
    vendor_list_version: NonNegativeInt = Field(
        default=0,
        description="Version of the GVL used to create this TCModel. "
        "Global Vendor List versions will be released periodically.",
    )
    num_custom_purposes: int = 0

    created: Optional[int] = None
    last_updated: Optional[int] = None

    special_feature_optins: List = Field(
        default=[],
        description="The TCF designates certain Features as special, that is, a CMP must afford the user a means to "
        "opt in to their use. These Special Features are published and numbered in the GVL separately from "
        "normal Features. Provides for up to 12 special features.",
    )

    purpose_consents: List = Field(
        default=[],
        description="Renamed from `PurposesAllowed` in TCF v1.1. The user’s consent value for each Purpose established "
        "on the legal basis of consent. Purposes are published in the Global Vendor List (see. [[GVL]]).",
    )

    purpose_legitimate_interests: List = Field(
        default=[],
        description="The user’s permission for each Purpose established on the legal basis of legitimate interest. "
        "If the user has exercised right-to-object for a purpose.",
    )

    publisher_consents: List = Field(
        default=[],
        description="The user’s consent value for each Purpose established on the legal basis of consent, for the "
        "publisher.  Purposes are published in the Global Vendor List.",
    )

    publisher_legitimate_interests: List = Field(
        default=[],
        description="The user’s permission for each Purpose established on the legal basis of legitimate interest.  "
        "If the user has exercised right-to-object for a purpose.",
    )

    publisher_custom_consents: List = Field(
        default=[],
        description="The user’s consent value for each Purpose established on the legal basis of consent, for the "
        "publisher.  Purposes are published in the Global Vendor List.",
    )

    publisher_custom_legitimate_interests: List = Field(
        default=[],
        description="The user’s permission for each Purpose established on the legal basis of legitimate interest.  "
        "If the user has exercised right-to-object for a purpose that is established in the publisher's "
        "custom purposes.",
    )

    custom_purposes: Dict = Field(
        default={},
        description="Set by a publisher if they wish to collect consent "
        "and LI Transparency for purposes outside of the TCF",
    )

    vendor_consents: List[int] = Field(
        default=[],
        description="Each [[Vendor]] is keyed by id. Their consent value is true if it is in the Vector",
    )

    vendor_legitimate_interests: List[int] = Field(
        default=[],
        description="Each [[Vendor]] is keyed by id. Whether their Legitimate Interests Disclosures have been "
        "established is stored as boolean.",
    )

    vendors_disclosed: List = Field(
        default=[],
        description=" The value included for disclosed vendors signals which vendors have been disclosed to the user "
        "in the interface surfaced by the CMP. This section content is required when writing a TC string "
        "to the global (consensu) scope. When a CMP has read from and is updating a TC string from the "
        "global consensu.org storage, the CMP MUST retain the existing disclosure information and only"
        " add information for vendors that it has disclosed that had not been disclosed by other CMPs in "
        "prior interactions with this device/user agent.",
    )

    vendors_allowed: List = Field(
        default=[],
        description="Signals which vendors the publisher permits to use OOB legal bases.",
    )

    publisher_restrictions: List = Field(
        default=[],
    )

    num_pub_restrictions: int = 0  # Hardcoded here for now

    @validator("publisher_country_code")
    def check_publisher_country_code(cls, publisher_country_code: str) -> str:
        """Validates that a publisher_country_code is an upper-cased two letter string"""
        upper_case_country_code = publisher_country_code.upper()
        pattern = r"^[A-Z]{2}$"
        if not re.match(pattern, upper_case_country_code):
            raise ValueError(
                "publisher_country_code must be a length-2 string of alpha characters"
            )

        return upper_case_country_code

    @validator("consent_language")
    def check_consent_language(cls, consent_language: str) -> str:
        """Forces consent language to be upper cased and no longer than 2 characters"""
        consent_language = consent_language.upper()[:2]
        if len(consent_language) < 2:
            raise ValueError("Consent language is less than two characters")
        return consent_language

    @validator("purpose_legitimate_interests")
    def filter_purpose_legitimate_interests(
        cls, purpose_legitimate_interests: List[int]
    ) -> List[int]:
        """Purpose 1 is never allowed to be true for legitimate interest
        As of TCF v2.2 purposes 3,4,5 & 6 are not allowed to be true.
        """
        forbidden_l_i_legitimate_interests = [1, 3, 4, 5, 6]
        return [
            li
            for li in purpose_legitimate_interests
            if li not in forbidden_l_i_legitimate_interests
        ]


def _build_vendor_consents_and_legitimate_interests(
    vendors: List[TCFVendorRecord], gvl_vendor_ids: List[int]
) -> Tuple[List, List]:
    """Construct the vendor_consents and vendor_legitimate_interests sections
    Only add the vendor id to the vendor consents list if one of its purposes
    has a consent legal basis, same for legitimate interests.
    """
    vendor_consents: List[int] = []
    vendor_legitimate_interests: List[int] = []

    for vendor in vendors:
        try:
            if int(vendor.id) not in gvl_vendor_ids:
                continue
        except ValueError:
            continue

        consent_purpose_ids: List[int] = [
            purpose.id
            for purpose in vendor.purposes
            if LegalBasisForProcessingEnum.CONSENT.value in purpose.legal_bases
        ]
        if consent_purpose_ids:
            vendor_consents.append(int(vendor.id))

        leg_int_purpose_ids: List[int] = [
            purpose.id
            for purpose in vendor.purposes
            if LegalBasisForProcessingEnum.LEGITIMATE_INTEREST.value
            in purpose.legal_bases
        ]

        # Ensure vendor doesn't have forbidden legint purpose set
        if leg_int_purpose_ids and not bool(
            set(leg_int_purpose_ids) & set(FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS)
        ):
            vendor_legitimate_interests.append(int(vendor.id))

    return vendor_consents, vendor_legitimate_interests


def _build_purpose_consent_and_legitimate_interests(
    purposes: List[TCFPurposeRecord],
) -> Tuple[List, List]:
    """Construct the purpose_consents and purpose_legitimate_interests sections"""

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


def _build_special_feature_opt_ins(special_features: List[TCFFeatureRecord]) -> List:
    """Construct the special_feature_opt_ins section"""
    special_feature_opt_ins: List[int] = []
    for special_feature in special_features:
        special_feature_opt_ins.append(special_feature.id)

    return special_feature_opt_ins


def _get_epoch_time() -> int:
    """Calculate the epoch time to be used for both created and updated_at

    TODO not sure why adding this extra 0 to the epoch time is necessary for it to decode properly
    Matches this: Math.round(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), new Date().getUTCDate())/100)
    """
    return int(datetime.utcnow().date().strftime("%s") + "0")


def transform_user_preference_to_boolean(preference: UserConsentPreference) -> bool:
    """Convert opt_in/acknowledge preferences to True and opt_out/other preferences to False"""
    return preference in [
        UserConsentPreference.opt_in,
        UserConsentPreference.acknowledge,
    ]


def build_tc_model(
    tcf_contents: TCFExperienceContents, preference: Optional[UserConsentPreference]
) -> TCModel:
    """
    Helper for building a TCModel that contains the information to build
    an accept-all or reject-all string, depending on the supplied preference.
    """
    with open(load_file([GVL_JSON_PATH]), "r", encoding="utf-8") as file:
        gvl = json.load(file)

    internal_gvl_vendor_ids: list[int] = [
        int(vendor_id) for vendor_id in gvl.get("vendors", {})
    ]

    if not preference:
        raise Exception(
            "Preference must be specified. Only accept or reject-all strings are currently supported."
        )

    consented: bool = transform_user_preference_to_boolean(preference)

    (
        vendor_consents,
        vendor_legitimate_interests,
    ) = _build_vendor_consents_and_legitimate_interests(
        tcf_contents.tcf_vendors, internal_gvl_vendor_ids
    )

    (
        purpose_consents,
        purpose_legitimate_interests,
    ) = _build_purpose_consent_and_legitimate_interests(tcf_contents.tcf_purposes)

    special_feature_opt_ins = _build_special_feature_opt_ins(
        tcf_contents.tcf_special_features
    )

    # Use the same date for created and lastUpdated
    current_time: int = _get_epoch_time()

    tc_model = TCModel(
        _gvl=gvl,
        cmp_id=CMP_ID,
        vendor_list_version=gvl.get("vendorListVersion"),
        policy_version=gvl.get("tcfPolicyVersion"),
        cmp_version=CMP_VERSION,
        consent_screen=CONSENT_SCREEN,
        vendors_disclosed=internal_gvl_vendor_ids,
        created=current_time,
        last_updated=current_time,
        vendor_consents=vendor_consents if consented else [],
        vendor_legitimate_interests=vendor_legitimate_interests if consented else [],
        purpose_consents=purpose_consents if consented else [],
        purpose_legitimate_interests=purpose_legitimate_interests
        if consented
        else [],  # TODO https://github.com/InteractiveAdvertisingBureau/iabtcf-es/blob/master/modules/core/src/encoder/SemanticPreEncoder.ts#L38
        special_feature_optins=special_feature_opt_ins if consented else [],
    )

    return tc_model


class TCFVersionHash(FidesSchema):
    """Minimal subset of the TCF experience details surfacing
    when consent should be resurfaced"""

    policy_version: int
    purpose_consents: List[int]
    purpose_legitimate_interests: List[int]
    special_feature_optins: List[int]
    vendor_consents: List[int]
    vendor_legitimate_interests: List[int]

    @root_validator()
    @classmethod
    def sort_lists(cls, values: Dict) -> Dict:
        """Verify lists are sorted ascending for repeatability"""
        for field, val in values.items():
            if isinstance(val, list):
                values[field] = sorted(val)
        return values

    class Config:
        extra = Extra.ignore


def _build_tcf_version_hash_model(
    tcf_contents: TCFExperienceContents,
) -> TCFVersionHash:
    """Given tcf_contents, constructs the TCFVersionHash model containing
    the raw contents to build the version_hash"""
    model = build_tc_model(tcf_contents, UserConsentPreference.opt_in)

    tcf_version_hash_schema: TCFVersionHash = TCFVersionHash(**model.dict())
    return tcf_version_hash_schema


def build_tcf_version_hash(tcf_contents: TCFExperienceContents) -> str:
    """Returns a 12-character version hash for TCF that should only change
    if there are updates to vendors, purposes, and special features sections or legal basis.
    """
    tcf_version_hash_model: TCFVersionHash = _build_tcf_version_hash_model(tcf_contents)
    json_str: str = json.dumps(tcf_version_hash_model.dict(), sort_keys=True)
    hashed_val: str = hashlib.sha256(json_str.encode()).hexdigest()
    return hashed_val[:12]  # Shortening string for usability, collision risk is low
