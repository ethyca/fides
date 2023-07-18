from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fideslang.models import Cookies as CookieSchema
from fideslang.validation import FidesKey
from pydantic import Extra, conlist, root_validator, validator

from fides.api.models.privacy_notice import ConsentMechanism, EnforcementLevel
from fides.api.models.privacy_notice import PrivacyNotice as PrivacyNoticeModel
from fides.api.models.privacy_notice import PrivacyNoticeRegion, UserConsentPreference
from fides.api.schemas.base_class import FidesSchema


class BaseConsentSchema(FidesSchema):
    name: Optional[str]
    description: Optional[str]
    internal_description: Optional[str]
    consent_mechanism: Optional[ConsentMechanism]
    enforcement_level: Optional[EnforcementLevel]
    has_gpc_flag: Optional[bool] = False


class PrivacyNotice(BaseConsentSchema):
    """
    Base for PrivacyNotice API objects

    All fields are optional, since pydantic allows subclasses to be
    stricter but not less strict
    """

    notice_key: Optional[FidesKey]
    origin: Optional[str]
    regions: Optional[conlist(PrivacyNoticeRegion, min_items=1)]  # type: ignore
    data_uses: Optional[conlist(str, min_items=1)]  # type: ignore
    disabled: Optional[bool] = False
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

    @root_validator(pre=True)
    def validate_notice_key(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the notice_key from the name if not supplied
        """
        if not values.get("notice_key"):
            values["notice_key"] = PrivacyNoticeModel.generate_notice_key(
                values.get("name")
            )

        return values

    @root_validator
    def validate_consent_mechanisms_and_display(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add some validation regarding where certain consent mechanisms must be displayed
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
    cookies: List[CookieSchema]


class UserSpecificConsentDetails(FidesSchema):
    default_preference: Optional[
        UserConsentPreference
    ]  # The default preference for this notice
    current_preference: Optional[
        UserConsentPreference
    ]  # The current saved preference for the given user if it exists
    outdated_preference: Optional[
        UserConsentPreference
    ]  # If no current preference, check if we have a preference saved for a previous version.
    current_served: Optional[
        bool
    ]  # Do we have a record of the most recent version of this notice being served to the user?
    outdated_served: Optional[
        bool
    ]  # Have we served an older version of this notice to the user?


class PrivacyNoticeResponseWithUserPreferences(
    PrivacyNoticeResponse, UserSpecificConsentDetails
):
    """
    If retrieving notices for a given user, also return the default preferences for that notice
    and any saved preferences.
    """


class TCFConsentRecord(BaseConsentSchema, UserSpecificConsentDetails):
    """Contents of a TCF Item generated at runtime"""

    key: str
    illustration: Optional[str]
    legal_basis: Optional[str]

    @root_validator
    def add_default_preference(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        consent_mechanism = values.get("consent_mechanism")
        if consent_mechanism == ConsentMechanism.opt_in:
            values["default_preference"] = UserConsentPreference.opt_out  # Intentional
        if consent_mechanism == ConsentMechanism.opt_out:
            values["default_preference"] = UserConsentPreference.opt_in  # Intentional
        if consent_mechanism == ConsentMechanism.notice_only:
            values["default_preference"] = UserConsentPreference.acknowledge

        return values

    class Config:
        use_enum_values = True


class TCFVendorConsentRecord(TCFConsentRecord):
    """Contents of a TCF Item generated at runtime"""

    data_uses: List[TCFConsentRecord] = []


class PrivacyNoticeHistorySchema(PrivacyNoticeCreation, PrivacyNoticeWithId):
    """
    An API representation of a PrivacyNoticeHistory used for response payloads
    """

    version: float
    privacy_notice_id: str

    class Config:
        use_enum_values = True
        orm_mode = True
