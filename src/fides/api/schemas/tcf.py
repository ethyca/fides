from typing import Any, Dict, List, Optional

from fideslang.gvl.models import MappedPurpose
from pydantic import root_validator

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_notice import UserSpecificConsentDetails


class TCFPurposeRecord(MappedPurpose, UserSpecificConsentDetails):
    vendors: List[str] = []  # Vendors that use this purpose

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """For TCF data uses, vendors, and features, the default preferences are just 'opt-out'"""
        values["default_preference"] = UserConsentPreference.opt_out

        return values

    class Config:
        use_enum_values = True


class EmbeddedPurpose(FidesSchema):
    id: int
    name: str


class TCFDataCategoryRecord(FidesSchema):
    id: str
    name: Optional[str]
    cookie: Optional[str]
    domain: Optional[str]
    duration: Optional[str]


class TCFVendorRecord(UserSpecificConsentDetails):
    id: str
    name: Optional[str]
    description: Optional[str]
    is_gvl: Optional[bool]
    purposes: List[EmbeddedPurpose] = []
    data_categories: List[TCFDataCategoryRecord] = []


class TCFFeatureRecord(UserSpecificConsentDetails):
    id: str
    name: Optional[str]


class TCFPurposeSave(FidesSchema):
    """Schema for saving a user's preference with respect to a TCF purpose"""

    id: int  # Identifier for the data use, vendor, or feature
    preference: UserConsentPreference
    served_notice_history_id: Optional[str]


class TCFPreferenceSave(FidesSchema):
    """Schema for saving a user's preference with respect to a vendor or feature"""

    id: str  # Identifier vendor or feature
    preference: UserConsentPreference
    served_notice_history_id: Optional[str]
