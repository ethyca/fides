from typing import Any, Dict, List, Optional

from pydantic import root_validator

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_notice import (
    BaseConsentSchema,
    UserSpecificConsentDetails,
)


class TCFConsentRecord(BaseConsentSchema, UserSpecificConsentDetails):
    """Schema for returning the contents of a TCF line item, generated at runtime"""

    id: str
    illustration: Optional[str]
    legal_basis: Optional[str]

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """For TCF data uses, vendors, and features, the default preferences are just 'opt-out'"""
        values["default_preference"] = UserConsentPreference.opt_out

        return values

    class Config:
        use_enum_values = True


class TCFVendorConsentRecord(TCFConsentRecord):
    """Schema for returning the contents of a TCF vendor, generated at runtime"""

    data_uses: List[TCFConsentRecord] = []


class TCFPreferenceSave(FidesSchema):
    """Schema for saving a user's preference with respect to a TCF Data use, vendor, or feature"""

    id: str  # Identifier for the data use, vendor, or feature
    preference: UserConsentPreference
    served_notice_history_id: Optional[str]
