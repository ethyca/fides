from typing import Optional

from fideslang.validation import FidesKey
from pydantic import conlist

from fides.api.custom_types import SafeStr
from fides.api.ops.models.privacy_notice import PrivacyNoticeRegion
from fides.api.ops.models.privacy_preference import RequestOrigin, UserConsentPreference
from fides.api.ops.schemas.privacy_notice import PrivacyNoticeHistorySchema
from fides.api.ops.schemas.redis_cache import Identity
from fides.lib.schemas.base_class import BaseSchema


class ConsentOptionCreate(BaseSchema):
    """Schema for saving the user's preference for a given notice"""

    privacy_notice_history_id: str
    preference: UserConsentPreference


class PrivacyPreferencesCreateWithCode(BaseSchema):
    """Schema for saving privacy preferences and accompanying user data
    including the verification code."""

    browser_identity: Identity
    code: Optional[SafeStr]
    preferences: conlist(ConsentOptionCreate, max_items=50)  # type: ignore
    policy_key: Optional[FidesKey]  # Will use default consent policy if not supplied
    request_origin: Optional[RequestOrigin]
    url_recorded: Optional[SafeStr]
    user_agent: Optional[SafeStr]
    user_geography: Optional[PrivacyNoticeRegion]


class MinimalPrivacyPreferenceHistorySchema(BaseSchema):
    """Minimal privacy preference history schema for building consent emails"""

    preference: UserConsentPreference
    privacy_notice_history: PrivacyNoticeHistorySchema


class CurrentPrivacyPreferenceSchema(BaseSchema):
    """Schema to represent the latest saved preference for a given privacy notice
    Note that we return the privacy notice *history* record here though which has the
    contents of the notice the user consented to at the time.
    """

    id: str
    preference: UserConsentPreference
    privacy_notice_history: PrivacyNoticeHistorySchema
    privacy_preference_history_id: str
