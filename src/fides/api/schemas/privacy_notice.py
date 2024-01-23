from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fideslang.models import Cookies as CookieSchema
from fideslang.validation import FidesKey
from pydantic import Extra, conlist, root_validator, validator

from fides.api.models.privacy_notice import ConsentMechanism, EnforcementLevel, Language
from fides.api.models.privacy_notice import PrivacyNotice as PrivacyNoticeModel
from fides.api.models.privacy_notice import PrivacyNoticeRegion, UserConsentPreference
from fides.api.schemas.base_class import FidesSchema


class NoticeTranslation(FidesSchema):
    language: Language
    title: Optional[str] = None
    description: Optional[str] = None

    class Config:
        use_enum_values = True


class PrivacyNotice(FidesSchema):
    """
    Base for PrivacyNotice API objects

    All fields are optional, since pydantic allows subclasses to be
    stricter but not less strict
    """

    name: Optional[str]
    notice_key: Optional[FidesKey]
    internal_description: Optional[str]
    origin: Optional[str]
    consent_mechanism: Optional[ConsentMechanism]
    data_uses: Optional[conlist(str, min_items=1)]  # type: ignore
    enforcement_level: Optional[EnforcementLevel]
    disabled: Optional[bool] = False
    has_gpc_flag: Optional[bool] = False
    translations: Optional[List[NoticeTranslation]] = []

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True
        orm_mode = True
        extra = Extra.ignore

    def validate_data_uses(self, valid_data_uses: List[str]) -> None:
        """
        Utility to validate that all specified data_uses exist as `DataUse`s.
        Raises a ValueError if an unknown `DataUse` is found.
        """
        for data_use in self.data_uses or []:
            if data_use not in valid_data_uses:
                raise ValueError(f"Unknown data_use '{data_use}'")

    @root_validator(pre=True)
    def validate_translations(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure no two translations with the same language are supplied
        """
        translations: List[Dict] = values.get("translations")
        if not translations:
            return values

        languages = [translation.get("language") for translation in translations]
        if len(languages) != len(set(languages)):
            raise ValueError(f"Multiple translations supplied for the same language")

        return values


class PrivacyNoticeCreation(PrivacyNotice):
    """
    An API representation of a PrivacyNotice.
    This model doesn't include an `id` so that it can be used for creation.
    It also establishes some fields _required_ for creation
    """

    name: str
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

    @root_validator(pre=True)
    def validate_translations(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure no two translations with the same language are supplied
        """
        translations: List[Dict] = values.get("translations")
        if not translations:
            return values

        languages = [translation.get("language") for translation in translations]
        if len(languages) != len(set(languages)):
            raise ValueError(f"Multiple translations supplied for the same language")

        return values


class PrivacyNoticeWithId(PrivacyNotice):
    """
    An API representation of a PrivacyNotice that includes an `id` field.
    Used to help model API responses and update payloads
    """

    id: str


class UserSpecificConsentDetails(FidesSchema):
    """Default preference for notice"""

    default_preference: Optional[
        UserConsentPreference
    ]  # The default preference for this notice or TCF component


class PrivacyNoticeResponse(UserSpecificConsentDetails, PrivacyNoticeWithId):
    """
    An API representation of a PrivacyNotice used for response payloads
    """

    created_at: datetime
    updated_at: datetime
    version: float
    privacy_notice_history_id: str
    cookies: List[CookieSchema]
    systems_applicable: bool = False


class PrivacyNoticeHistorySchema(PrivacyNoticeCreation, PrivacyNoticeWithId):
    """
    An API representation of a PrivacyNoticeHistory used for response payloads
    """

    version: float
    privacy_notice_id: str

    class Config:
        use_enum_values = True
        orm_mode = True
