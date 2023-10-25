from typing import Any, Dict, List, Literal, Optional

from fideslang.gvl import (
    GVL_FEATURES,
    GVL_SPECIAL_FEATURES,
    MAPPED_PURPOSES,
    MAPPED_SPECIAL_PURPOSES,
)
from fideslang.gvl.models import Feature, MappedPurpose
from pydantic import AnyUrl, Field, root_validator, validator

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_notice import UserSpecificConsentDetails


class EmbeddedVendor(FidesSchema):
    """Sparse details for an embedded vendor beneath a purpose or feature section. Read-only."""

    id: str
    name: str


class NonVendorSection(UserSpecificConsentDetails):
    """Common details for non-vendor TCF sections.  Includes previously-saved preferences and
    records where consent was previously served if applicable."""

    vendors: List[EmbeddedVendor] = []  # Vendors that use this TCF attribute
    systems: List[EmbeddedVendor] = []  # Systems that use this TCF attribute


class TCFPurposeConsentRecord(NonVendorSection, MappedPurpose):
    """Schema for a TCF Purpose with Consent Legal Basis returned in the TCF Overlay Experience"""

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for purposes with legal basis of consent is opt-out"""
        values["default_preference"] = UserConsentPreference.opt_out

        return values


class TCFPurposeLegitimateInterestsRecord(NonVendorSection, MappedPurpose):
    """Schema for a TCF Purpose with Legitimate Interests Legal Basis returned in the TCF Overlay Experience"""

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for purposes with legal basis of legitimate interests is opt-in"""
        values["default_preference"] = UserConsentPreference.opt_in

        return values


class TCFSpecialPurposeRecord(NonVendorSection, MappedPurpose):
    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for special purposes is acknowledge"""
        values["default_preference"] = UserConsentPreference.acknowledge

        return values


class EmbeddedLineItem(FidesSchema):
    """Sparse details for an embedded TCF line item within another TCF component. Read-only."""

    id: int
    name: str


class EmbeddedPurpose(EmbeddedLineItem):
    """Sparse details for an embedded purpose beneath a system or vendor section.  Read-only."""

    retention_period: Optional[str]


class CommonVendorFields(FidesSchema):
    """Fields shared between the three vendor sections of the TCF Experience"""

    id: str
    has_vendor_id: Optional[bool]
    name: Optional[str]
    description: Optional[str]


class TCFVendorConsentRecord(UserSpecificConsentDetails, CommonVendorFields):
    """Schema for a TCF Vendor with Consent legal basis"""

    purpose_consents: List[EmbeddedPurpose] = []

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for vendor with legal basis of consent is opt-out"""
        values["default_preference"] = UserConsentPreference.opt_out

        return values


class TCFVendorLegitimateInterestsRecord(
    UserSpecificConsentDetails, CommonVendorFields
):
    """Schema for a TCF Vendor with Legitimate interests legal basis"""

    purpose_legitimate_interests: List[EmbeddedPurpose] = []

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for vendor with legal basis of leg interests is opt-in"""
        values["default_preference"] = UserConsentPreference.opt_in

        return values


class TCFVendorRelationships(CommonVendorFields):
    """Collects the other relationships for a given vendor - no preferences are saved here"""

    special_purposes: List[EmbeddedPurpose] = []
    features: List[EmbeddedLineItem] = []
    special_features: List[EmbeddedLineItem] = []
    cookie_max_age_seconds: Optional[int]
    uses_cookies: Optional[bool]
    cookie_refresh: Optional[bool]
    uses_non_cookie_access: Optional[bool]
    legitimate_interest_disclosure_url: Optional[AnyUrl]
    privacy_policy_url: Optional[AnyUrl]


class TCFFeatureRecord(NonVendorSection, Feature):
    """Schema for a TCF Feature: returned in the TCF Overlay Experience"""

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for features is acknowledge"""
        values["default_preference"] = UserConsentPreference.acknowledge

        return values


class TCFSpecialFeatureRecord(NonVendorSection, Feature):
    """Schema for a TCF Special Feature: returned in the TCF Overlay Experience"""

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for special features is acknowledge"""
        values["default_preference"] = UserConsentPreference.opt_out

        return values


class TCFPreferenceSaveBase(FidesSchema):
    """Base schema for saving individual TCF component preferences"""

    id: int
    preference: UserConsentPreference
    served_notice_history_id: Optional[str]


class TCFPurposeSave(TCFPreferenceSaveBase):
    """Schema for saving preferences with respect to a TCF Purpose"""

    @validator("id")
    @classmethod
    def validate_purpose_id(cls, value: int) -> int:
        """
        Validate purpose id is valid
        """
        if value not in MAPPED_PURPOSES:
            raise ValueError(
                f"Cannot save preferences against invalid purpose id: '{value}'"
            )
        return value


class TCFSpecialPurposeSave(TCFPreferenceSaveBase):
    """Schema for saving preferences with respect to a TCF Special Purpose"""

    @validator("id")
    @classmethod
    def validate_special_purpose_id(cls, value: int) -> int:
        """
        Validate special purpose id is valid
        """
        if value not in MAPPED_SPECIAL_PURPOSES:
            raise ValueError(
                f"Cannot save preferences against invalid special purpose id: '{value}'"
            )
        return value


class TCFVendorSave(FidesSchema):
    """Base schema for saving preferences with respect to a TCF Vendor or a System
    TODO: TCF Add validation for allowable vendors (in GVL or dictionary?)
    """

    id: str
    preference: UserConsentPreference
    served_notice_history_id: Optional[str]


class TCFFeatureSave(TCFPreferenceSaveBase):
    """Schema for saving a user's preference with respect to a TCF feature"""

    @validator("id")
    @classmethod
    def validate_feature_id(cls, value: int) -> int:
        """
        Validate feature id is valid
        """
        if value not in GVL_FEATURES:
            raise ValueError(
                f"Cannot save preferences against invalid feature id: '{value}'"
            )
        return value


class TCFSpecialFeatureSave(TCFPreferenceSaveBase):
    """Schema for saving a user's preference with respect to a TCF special feature"""

    @validator("id")
    @classmethod
    def validate_special_feature_id(cls, value: int) -> int:
        """
        Validate special feature id is valid
        """
        if value not in GVL_SPECIAL_FEATURES:
            raise ValueError(
                f"Cannot save preferences against invalid special feature id: '{value}'"
            )
        return value


BinaryChoice = Literal[0, 1]


class TCMobileData(FidesSchema):
    """Pre-parsed TC data and TC string for a CMP SDK:

    https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework/blob/master/TCFv2/IAB%20Tech%20Lab%20-%20CMP%20API%20v2.md#in-app-details
    """

    IABTCF_CmpSdkID: Optional[int] = Field(
        description="The unsigned integer ID of CMP SDK"
    )
    IABTCF_CmpSdkVersion: Optional[int] = Field(
        description="The unsigned integer version number of CMP SDK"
    )
    IABTCF_PolicyVersion: Optional[int] = Field(
        description="The unsigned integer representing the version of the TCF that these consents adhere to."
    )
    IABTCF_gdprApplies: Optional[BinaryChoice] = Field(
        description="1: GDPR applies in current context, 0 - GDPR does not apply in current context, None=undetermined"
    )
    IABTCF_PublisherCC: Optional[str] = Field(
        default="AA", description="Two-letter ISO 3166-1 alpha-2 code"
    )
    IABTCF_PurposeOneTreatment: Optional[BinaryChoice] = Field(
        description="Vendors can use this value to determine whether consent for purpose one is required. 0: "
        "no special treatment. 1: purpose one not disclosed"
    )
    IABTCF_UseNonStandardTexts: Optional[BinaryChoice] = Field(
        description="1 - CMP uses customized stack descriptions and/or modified or supplemented standard illustrations."
        "0 - CMP did not use a non-standard stack desc. and/or modified or supplemented Illustrations"
    )
    IABTCF_TCString: Optional[str] = Field(description="Fully encoded TC string")
    IABTCF_VendorConsents: Optional[str] = Field(
        description="Binary string: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the "
        "consent status for Vendor ID n+1; false and true respectively. eg. '1' at index 0 is consent "
        "true for vendor ID 1"
    )
    IABTCF_VendorLegitimateInterests: Optional[str] = Field(
        description="Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the "
        "legitimate interest status for Vendor ID n+1; false and true respectively. eg. '1' at index 0 is "
        "legitimate interest established true for vendor ID 1"
    )
    IABTCF_PurposeConsents: Optional[str] = Field(
        description="Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the "
        "consent status for purpose ID n+1; false and true respectively. eg. '1' at index 0 is consent "
        "true for purpose ID 1"
    )
    IABTCF_PurposeLegitimateInterests: Optional[str] = Field(
        description="Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the"
        " legitimate interest status for purpose ID n+1; false and true respectively. eg. '1' at index 0 "
        "is legitimate interest established true for purpose ID 1"
    )
    IABTCF_SpecialFeaturesOptIns: Optional[str] = Field(
        description="Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates "
        "the opt-in status for special feature ID n+1; false and true respectively. eg. '1' at index 0 is "
        "opt-in true for special feature ID 1"
    )
    # IABTCF_PublisherRestrictions{ID}  # TODO this field has dynamic keys.  Add when we start surfacing publisher restrictions
    IABTCF_PublisherConsent: Optional[str] = None
    IABTCF_PublisherLegitimateInterests: Optional[str] = None
    IABTCF_PublisherCustomPurposesConsents: Optional[str] = None
    IABTCF_PublisherCustomPurposesLegitimateInterests: Optional[str] = None
    IABTCF_AddtlConsent: Optional[
        str
    ] = None  # TODO: placholder for Google Additional Consent Mode string, needs to be populated!
