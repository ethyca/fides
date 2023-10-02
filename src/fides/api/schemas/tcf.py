from typing import Any, Dict, List, Optional

from fideslang.gvl import (
    GVL_FEATURES,
    GVL_SPECIAL_FEATURES,
    MAPPED_PURPOSES,
    MAPPED_SPECIAL_PURPOSES,
)
from fideslang.gvl.models import Feature, MappedPurpose
from pydantic import root_validator, validator

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_notice import UserSpecificConsentDetails


class TCFSavedandServedDetails(UserSpecificConsentDetails):
    """Default Schema that combines TCF details with whether a consent item was
    previously saved or served."""

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """For TCF components, the default preferences are just 'opt-out'"""
        values["default_preference"] = UserConsentPreference.opt_out

        return values

    class Config:
        use_enum_values = True


class EmbeddedVendor(FidesSchema):
    """Sparse details for an embedded vendor beneath a purpose or feature section. Read-only."""

    id: str
    name: str


class NonVendorSection(TCFSavedandServedDetails):
    vendors: List[EmbeddedVendor] = []  # Vendors that use this TCF attribute
    systems: List[EmbeddedVendor] = []  # Systems that use this TCF attribute


class TCFPurposeConsentRecord(MappedPurpose, NonVendorSection):
    """Schema for a TCF Purpose with Consent Legal Basis returned in the TCF Overlay Experience"""

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for purposes with legal basis of consent is opt-out"""
        values["default_preference"] = UserConsentPreference.opt_out

        return values


class TCFPurposeLegitimateInterestsRecord(MappedPurpose, NonVendorSection):
    """Schema for a TCF Purpose with Legitimate Interests Legal Basis returned in the TCF Overlay Experience"""

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for purposes with legal basis of legitimate interests is opt-int"""
        values["default_preference"] = UserConsentPreference.opt_in

        return values


class TCFSpecialPurposeRecord(MappedPurpose, NonVendorSection):
    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for special purposes is acknowledge"""
        values["default_preference"] = UserConsentPreference.acknowledge

        return values


class EmbeddedLineItem(FidesSchema):
    """Sparse details for an embedded TCF line item within another TCF component. Read-only."""

    id: int
    name: str


class VendorConsentPreference(UserSpecificConsentDetails):
    id: str

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for vendor with legal basis of consent is opt-out"""
        values["default_preference"] = UserConsentPreference.opt_out

        return values


class VendorLegitimateInterestsPreference(UserSpecificConsentDetails):
    id: str

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for vendor with legal basis of leg interests is opt-in"""
        values["default_preference"] = UserConsentPreference.opt_in

        return values


class TCFVendorRecord(FidesSchema):
    """Schema for a TCF Vendor or system: returned in the TCF Overlay Experience"""

    id: str
    has_vendor_id: bool
    name: Optional[str]
    description: Optional[str]
    consent_purposes: List[EmbeddedLineItem] = []
    legitimate_interests_purposes: List[EmbeddedLineItem] = []
    special_purposes: List[EmbeddedLineItem] = []
    features: List[EmbeddedLineItem] = []
    special_features: List[EmbeddedLineItem] = []
    consent_preference: VendorConsentPreference
    legitimate_interests_preference: VendorLegitimateInterestsPreference


class TCFFeatureRecord(Feature, NonVendorSection):
    """Schema for a TCF Feature: returned in the TCF Overlay Experience"""

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Default preference for features is acknowledge"""
        values["default_preference"] = UserConsentPreference.acknowledge

        return values


class TCFSpecialFeatureRecord(Feature, NonVendorSection):
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
