from typing import Any, Dict, List, Optional

from fideslang.gvl.models import MappedPurpose
from pydantic import root_validator

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_notice import UserSpecificConsentDetails


class TCFSavedandServedDetails(UserSpecificConsentDetails):
    """Default Schema that is supplements provided TCF details with whether a consent item was
    previously saved or served."""

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """For TCF purposes/special purposes, vendors, features, and special features,
        the default preferences are just 'opt-out'"""
        values["default_preference"] = UserConsentPreference.opt_out

        return values

    class Config:
        use_enum_values = True


class EmbeddedVendor(FidesSchema):
    """Sparse details for an embedded vendor.  Read-only."""

    id: str
    name: str


class TCFPurposeRecord(MappedPurpose, TCFSavedandServedDetails):
    """Schema for a TCF Purpose or a Special Purpose: returned in the TCF Overlay Experience"""

    vendors: List[EmbeddedVendor] = []  # Vendors that use this purpose


class EmbeddedPurpose(FidesSchema):
    """Sparse details for an embedded purpose or special purpose. Read-only."""

    id: int
    name: str


class TCFDataCategoryRecord(FidesSchema):
    """Details for data categories on systems: Read-only"""

    id: str
    name: Optional[str]
    cookie: Optional[str]
    domain: Optional[str]
    duration: Optional[str]


class TCFVendorRecord(TCFSavedandServedDetails):
    """Schema for a TCF Vendor: returned in the TCF Overlay Experience"""

    id: str
    name: Optional[str]
    description: Optional[str]
    is_gvl: Optional[bool]
    purposes: List[EmbeddedPurpose] = []
    special_purposes: List[EmbeddedPurpose] = []
    data_categories: List[TCFDataCategoryRecord] = []


class TCFFeatureRecord(TCFSavedandServedDetails):
    """Schema for a TCF Feature or a special feature: returned in the TCF Overlay Experience"""

    id: int
    name: Optional[str]


class TCFPreferenceSave(FidesSchema):
    """Schema for saving a user's preference with respect to a component with an integer identifier on a TCF overlay:
    either a purpose, special purpose, feature, or special feature"""

    id: int
    preference: UserConsentPreference
    served_notice_history_id: Optional[str]


class TCFVendorSave(FidesSchema):
    """Schema for saving a user's preference with respect to a vendor, which has a string identifier"""

    id: str
    preference: UserConsentPreference
    served_notice_history_id: Optional[str]
