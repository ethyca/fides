import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from pydantic import Field, NonNegativeInt, PositiveInt, root_validator, validator

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.tcf import (
    TCFSpecialFeatureRecord,
    TCFVendorConsentRecord,
    TCFVendorLegitimateInterestsRecord,
)
from fides.api.util.tcf.ac_string import build_ac_vendor_consents
from fides.api.util.tcf.tcf_experience_contents import (
    AC_PREFIX,
    GVL_PREFIX,
    TCFExperienceContents,
    load_gvl,
)

CMP_ID: int = 407
CMP_VERSION = 1
CONSENT_SCREEN = 1  # TODO On which 'screen' consent was captured; this is a CMP proprietary number encoded into the TC string

FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS = [1, 3, 4, 5, 6]
gvl: Dict = load_gvl()


def universal_vendor_id_to_gvl_id(universal_vendor_id: str) -> int:
    """Converts a universal gvl vendor id to a vendor id

    For example, converts "gvl.42" to integer 42.
    Throws a ValueError if the id cannot be converted to an integer or if this is an AC Vendor ID

    We store vendor ids as a universal vendor id internally, but need to strip this off when building TC strings.
    """
    if universal_vendor_id.startswith(AC_PREFIX):
        raise ValueError("Skipping AC Vendor ID")
    return int(universal_vendor_id.lstrip(GVL_PREFIX))


class TCModel(FidesSchema):
    """Base internal TCF schema to store and validate key details from which to later build the TC String
    and AC Strings
    """

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
        "will be included if the publish wishes to not allow these vendors they should set this to false.",
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
        "expected by Policy.  `true` Purpose 1 not disclosed at all. CMPs use PublisherCC to indicate the "
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
        "on the legal basis of consent. Purposes are published in the Global Vendor List.",
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
        description="The user’s permission for each Purpose established on the legal basis of legitimate interest, for "
        "the publisher. If the user has exercised right-to-object for a purpose.",
    )

    publisher_custom_consents: List = Field(
        default=[],
        description="The user’s consent value for each custom Purpose established on the legal basis of consent, "
        "for the publisher.  Purposes are published in the Global Vendor List.",
    )

    publisher_custom_legitimate_interests: List = Field(
        default=[],
        description="The user’s permission for each custom Purpose established on the legal basis of legitimate "
        "interest.  If the user has exercised right-to-object for a purpose that is established in "
        "the publisher's custom purposes.",
    )

    custom_purposes: Dict = Field(
        default={},
        description="Set by a publisher if they wish to collect consent "
        "and LI Transparency for purposes outside of the TCF",
    )

    vendor_consents: List[int] = Field(
        default=[],
        description="Each Vendor is keyed by id. Their consent value is true if it is in the Vector",
    )

    vendor_legitimate_interests: List[int] = Field(
        default=[],
        description="Each Vendor is keyed by id. Whether their Legitimate Interests Disclosures have been "
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

    # TODO: no way to set this currently
    publisher_restrictions: List = Field(
        default=[],
    )

    num_pub_restrictions: int = 0  # Hardcoded here for now

    ac_vendor_consents: List[int] = Field(
        default=[],
        description="A list of Google's Additional Consent Vendors for which the customer has opted in. These "
        "are consented Google Ad Tech Providers that are not registered with IAB",
    )

    @validator("publisher_country_code")
    def check_publisher_country_code(cls, publisher_country_code: str) -> str:
        """Validates that a publisher_country_code is an upper-cased two letter string"""
        upper_case_country_code: str = publisher_country_code.upper()
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
        return [
            li
            for li in purpose_legitimate_interests
            if li not in FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS
        ]

    @root_validator()
    @classmethod
    def vendor_legal_basis_validation(cls, values: Dict) -> Dict:
        """Multiple operations in the root_validator:

        - Remove any vendor ids from vendor_consents if the legal basis is not allowed
        - Remove any vendor ids from vendor_legitimate_interests if the legal basis is not allowed
        """
        is_service_specific: Optional[bool] = values.get("is_service_specific")

        values["vendor_consents"] = _validate_vendor_legal_basis_fields(
            values.get("vendor_consents", []),
            corresponding_gvl_key="purposes",
            is_service_specific=is_service_specific,
        )

        values["vendor_legitimate_interests"] = _validate_vendor_legal_basis_fields(
            values.get("vendor_legitimate_interests", []),
            corresponding_gvl_key="legIntPurposes",
            is_service_specific=is_service_specific,
        )

        return values


def _validate_vendor_legal_basis_fields(
    vendor_list: List[int],
    corresponding_gvl_key: str,
    is_service_specific: Optional[bool],
) -> List[int]:
    """Helper for looping through legal basis vendor lists and removing vendors where the legal basis
    is not permitted"""
    to_remove: List[int] = []
    for vendor_id in vendor_list:
        vendor_record: Optional[Dict] = gvl.get("vendors", {}).get(str(vendor_id))

        if not vendor_record:
            # This vendor isn't in the GVLvalues.get("is_service_specific")
            # , we've got to remove it!
            to_remove.append(vendor_id)
            continue

        if vendor_record.get(corresponding_gvl_key):
            # The vendor has the matching legal basis, so this is fine!
            continue

        if (
            corresponding_gvl_key == "legIntPurposes"
            and not vendor_record.get("purposes")
            and vendor_record.get("specialPurposes")
        ):
            # While vendor record is missing legIntPurposes, it has specialPurposes, so this is fine!
            # Vendors only declaring special purposes must have their legitimate interest vendor bit set.
            continue

        if not is_service_specific or not vendor_record.get("flexiblePurposes"):
            # Either this is a globally scoped string, in which cases flexible purposes don't have an effect,
            # or there are no flexible purposes at all.  We have to remove the vendor from the legal bases list.
            to_remove.append(vendor_id)
            continue

        # TODO once adding publisher_restrictions to the TCModel are supported, check if there is a publisher
        # restriction value that would enable this vendor to have the override preferred basis.
        # For now, assume there are no restrictions defined:
        to_remove.append(vendor_id)

    return [v_id for v_id in vendor_list if v_id not in to_remove]


def _build_vendor_consents_and_legitimate_interests(
    vendor_consents: List[TCFVendorConsentRecord],
    vendor_legitimate_interests: List[TCFVendorLegitimateInterestsRecord],
) -> Tuple[List, List]:
    """Construct the vendor_consents and vendor_legitimate_interests sections
    Only add the vendor id to the vendor consents list if one of its purposes
    has a consent legal basis, same for legitimate interests.

    Later, in the TCModel construction, we validate if the vendor is allowed to have
    this legal basis
    """
    vendor_consent_ids: List[int] = []
    vendor_legitimate_interest_ids: List[int] = []

    for vendor_consent in vendor_consents:
        try:
            vendor_consent_id: int = universal_vendor_id_to_gvl_id(vendor_consent.id)
        except ValueError:
            # Early check that filters out non-integer vendor ids.  Later we'll run a separate
            # check that ensures this id is also in the gvl.
            continue

        if vendor_consent.purpose_consents:
            # This vendor should only be in "vendor_consents" in the first place, if consent_purposes is populated.
            # This is just to check
            vendor_consent_ids.append(vendor_consent_id)

    for vendor_legitimate_interest in vendor_legitimate_interests:
        try:
            vendor_li_id: int = universal_vendor_id_to_gvl_id(
                vendor_legitimate_interest.id
            )
        except ValueError:
            # Early check that filters out non-integer vendor ids.  Later we'll run a separate
            # check that ensures this id is also in the gvl.
            continue

        leg_int_purpose_ids: List[int] = [
            purpose.id
            for purpose in vendor_legitimate_interest.purpose_legitimate_interests
        ]

        # Ensure vendor doesn't have forbidden legint purpose set
        if leg_int_purpose_ids and not bool(
            set(leg_int_purpose_ids) & set(FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS)
        ):
            vendor_legitimate_interest_ids.append(vendor_li_id)

    return vendor_consent_ids, vendor_legitimate_interest_ids


def _build_special_feature_opt_ins(
    special_features: List[TCFSpecialFeatureRecord],
) -> List[int]:
    """Construct the special_feature_opt_ins section"""
    special_feature_opt_ins: List[int] = []
    for special_feature in special_features:
        special_feature_opt_ins.append(special_feature.id)

    return special_feature_opt_ins


def _build_vendors_disclosed(tcf_contents: TCFExperienceContents) -> List[int]:
    """
    Returns the vendor ids that we surface in the TCF Experience, provided they show up in the GVL.

    The DisclosedVendors is an optional TC String segment that records which vendors have been disclosed to a
    given user by a CMP. It may be used by a CMP while storing TC Strings, but must not be included in the TC String
    when returned by the CMP API."""
    all_vendor_ids: List[int] = [int(vendor_id) for vendor_id in gvl.get("vendors", {})]
    vendors_disclosed = set()

    vendor_main_lists: List[List] = [
        tcf_contents.tcf_vendor_consents,
        tcf_contents.tcf_vendor_legitimate_interests,
        tcf_contents.tcf_vendor_relationships,
    ]

    for vendor_list in vendor_main_lists:
        for vendor in vendor_list:
            try:
                vendor_id: int = universal_vendor_id_to_gvl_id(vendor.id)
            except ValueError:
                continue
            if vendor_id in all_vendor_ids:
                vendors_disclosed.add(vendor_id)

    return sorted(list(vendors_disclosed))


def _get_epoch_time() -> int:
    """Calculate the epoch time to be used for both created and updated_at

    Matches this: Math.round(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), new Date().getUTCDate())/100)
    Had to add an extra "0" to get it to match.
    """
    return int(datetime.utcnow().date().strftime("%s") + "0")


def transform_user_preference_to_boolean(preference: UserConsentPreference) -> bool:
    """Convert opt_in/acknowledge preferences to True and opt_out/other preferences to False"""
    return preference in [
        UserConsentPreference.opt_in,
        UserConsentPreference.acknowledge,
    ]


def convert_tcf_contents_to_tc_model(
    tcf_contents: TCFExperienceContents, preference: Optional[UserConsentPreference]
) -> TCModel:
    """
    Helper for building a TCModel from TCFExperienceContents that contains the prerequisite information to build
    an accept-all or reject-all fides string, with TC and AC sections, depending on the supplied preference.
    """
    if not preference:
        # Dev-level error
        raise Exception(
            "Overall preference must be specified. Only accept or reject-all strings are currently supported."
        )

    consented: bool = transform_user_preference_to_boolean(preference)

    (
        vendor_consents,
        vendor_legitimate_interests,
    ) = _build_vendor_consents_and_legitimate_interests(
        tcf_contents.tcf_vendor_consents, tcf_contents.tcf_vendor_legitimate_interests
    )

    purpose_consents: List[int] = [
        purpose.id for purpose in tcf_contents.tcf_purpose_consents
    ]
    purpose_legitimate_interests: List[int] = [
        purpose.id for purpose in tcf_contents.tcf_purpose_legitimate_interests
    ]

    special_feature_opt_ins: List[int] = _build_special_feature_opt_ins(
        tcf_contents.tcf_special_features
    )

    current_time: int = _get_epoch_time()

    tc_model = TCModel(
        created=current_time,
        last_updated=current_time,
        cmp_id=CMP_ID,
        cmp_version=CMP_VERSION,
        consent_screen=CONSENT_SCREEN,
        vendor_list_version=gvl.get("vendorListVersion"),
        policy_version=gvl.get("tcfPolicyVersion"),
        special_feature_optins=special_feature_opt_ins if consented else [],
        purpose_consents=purpose_consents if consented else [],
        purpose_legitimate_interests=purpose_legitimate_interests if consented else [],
        vendor_consents=vendor_consents if consented else [],
        vendor_legitimate_interests=vendor_legitimate_interests if consented else [],
        vendors_disclosed=_build_vendors_disclosed(tcf_contents),
        ac_vendor_consents=build_ac_vendor_consents(tcf_contents, preference),
    )

    return tc_model
