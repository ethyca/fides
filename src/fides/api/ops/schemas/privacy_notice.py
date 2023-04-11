from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import Extra, conlist

from fides.api.custom_types import SafeStr
from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNoticeRegion,
)
from fides.api.ops.schemas.base_class import BaseSchema


class PrivacyNotice(BaseSchema):
    """
    Base for PrivacyNotice API objects

    All fields are optional, since pydantic allows subclasses to be
    stricter but not less strict
    """

    name: Optional[SafeStr]
    description: Optional[SafeStr]
    internal_description: Optional[SafeStr]
    origin: Optional[SafeStr]
    regions: Optional[conlist(PrivacyNoticeRegion, min_items=1)]  # type: ignore
    consent_mechanism: Optional[ConsentMechanism]
    data_uses: Optional[conlist(SafeStr, min_items=1)]  # type: ignore
    enforcement_level: Optional[EnforcementLevel]
    disabled: Optional[bool] = False
    has_gpc_flag: Optional[bool] = False
    displayed_in_privacy_center: Optional[bool] = True
    displayed_in_overlay: Optional[bool] = True
    displayed_in_api: Optional[bool] = True

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True
        orm_mode = True
        extra = Extra.forbid

    def validate_data_uses(self, valid_data_uses: List[str]) -> None:
        """
        Utility to validate that all specified data_uses exist as `DataUse`s.
        Raises a ValueError if an unknown `DataUse` is found.
        """
        for data_use in self.data_uses or []:
            if data_use not in valid_data_uses:
                raise ValueError(f"Unknown data_use '{data_use}'")


class PrivacyNoticeCreation(PrivacyNotice):
    """
    An API representation of a PrivacyNotice.
    This model doesn't include an `id` so that it can be used for creation.
    It also establishes some fields _required_ for creation
    """

    name: SafeStr
    regions: conlist(PrivacyNoticeRegion, min_items=1)  # type: ignore
    consent_mechanism: ConsentMechanism
    data_uses: conlist(SafeStr, min_items=1)  # type: ignore
    enforcement_level: EnforcementLevel


class PrivacyNoticeWithId(PrivacyNotice):
    """
    An API representation of a PrivacyNotice that includes an `id` field.
    Used to help model API responses and update payloads
    """

    id: str


class PrivacyNoticeResponse(PrivacyNoticeWithId):
    """
    An API representation of a PrivacyNotice used for response payloads
    """

    created_at: datetime
    updated_at: datetime
    version: float
    privacy_notice_history_id: str


class PrivacyNoticeHistorySchema(PrivacyNoticeCreation, PrivacyNoticeWithId):
    """
    An API representation of a PrivacyNoticeHistory used for response payloads
    """

    version: float
    privacy_notice_id: str

    class Config:
        use_enum_values = True
        orm_mode = True
