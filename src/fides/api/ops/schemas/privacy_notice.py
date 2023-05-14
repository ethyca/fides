from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Extra, conlist, root_validator, validator

from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNoticeRegion,
)
from fides.api.ops.schemas.base_class import FidesSchema


class PrivacyNotice(FidesSchema):
    """
    Base for PrivacyNotice API objects

    All fields are optional, since pydantic allows subclasses to be
    stricter but not less strict
    """

    name: Optional[str]
    description: Optional[str]
    internal_description: Optional[str]
    origin: Optional[str]
    regions: Optional[conlist(PrivacyNoticeRegion, min_items=1)]  # type: ignore
    consent_mechanism: Optional[ConsentMechanism]
    data_uses: Optional[conlist(str, min_items=1)]  # type: ignore
    enforcement_level: Optional[EnforcementLevel]
    disabled: Optional[bool] = False
    has_gpc_flag: Optional[bool] = False
    displayed_in_privacy_center: Optional[bool] = False
    displayed_in_overlay: Optional[bool] = False
    displayed_in_api: Optional[bool] = False

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True
        orm_mode = True
        extra = Extra.forbid

    @validator("regions")
    @classmethod
    def validate_regions(
        cls, regions: List[PrivacyNoticeRegion]
    ) -> List[PrivacyNoticeRegion]:
        """Assert regions aren't duplicated.  Without this, duplications get flagged as misleading duplicate data uses"""
        if len(regions) != len(set(regions)):
            raise ValueError("Duplicate regions found.")
        return regions

    def validate_data_uses(self, valid_data_uses: List[str]) -> None:
        """
        Utility to validate that all specified data_uses exist as `DataUse`s.
        Raises a ValueError if an unknown `DataUse` is found.
        """
        for data_use in self.data_uses or []:
            if data_use not in valid_data_uses:
                raise ValueError(f"Unknown data_use '{data_use}'")

    @root_validator
    def validate_consent_mechanisms_and_display(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add some validation on where certain consent mechanisms must be displayed
        """
        consent_mechanism: Optional[str] = values.get("consent_mechanism")
        displayed_in_overlay: Optional[bool] = values.get("displayed_in_overlay")
        displayed_in_privacy_center: Optional[bool] = values.get(
            "displayed_in_privacy_center"
        )

        if (
            consent_mechanism == ConsentMechanism.opt_in.value
            and not displayed_in_overlay
        ):
            raise ValueError("Opt-in notices must be served in an overlay.")

        if consent_mechanism == ConsentMechanism.opt_out.value and not (
            displayed_in_privacy_center or displayed_in_overlay
        ):
            raise ValueError(
                "Opt-out notices must be served in an overlay or the privacy center."
            )

        if (
            consent_mechanism == ConsentMechanism.notice_only.value
            and not displayed_in_overlay
        ):
            raise ValueError("Notice-only notices must be served in an overlay.")

        return values


class PrivacyNoticeCreation(PrivacyNotice):
    """
    An API representation of a PrivacyNotice.
    This model doesn't include an `id` so that it can be used for creation.
    It also establishes some fields _required_ for creation
    """

    name: str
    regions: conlist(PrivacyNoticeRegion, min_items=1)  # type: ignore
    consent_mechanism: ConsentMechanism
    data_uses: conlist(str, min_items=1)  # type: ignore
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
