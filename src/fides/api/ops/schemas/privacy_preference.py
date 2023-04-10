from typing import Dict, List, Optional

from fideslang.validation import FidesKey

from fides.api.custom_types import SafeStr
from fides.api.ops.models.privacy_notice import PrivacyNoticeRegion
from fides.api.ops.models.privacy_preference import RequestOrigin, UserConsentPreference
from fides.api.ops.models.privacy_request import ExecutionLogStatus
from fides.api.ops.schemas.privacy_notice import PrivacyNoticeHistorySchema
from fides.api.ops.schemas.privacy_request import PrivacyRequestResponse
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
    preferences: List[ConsentOptionCreate]
    policy_key: Optional[FidesKey]  # Will use default consent policy if not supplied
    request_origin: Optional[RequestOrigin]
    url_recorded: Optional[SafeStr]
    user_agent: Optional[SafeStr]
    user_geography: Optional[PrivacyNoticeRegion]


class MinimalPrivacyPreferenceHistorySchema(BaseSchema):
    """Minimal privacy preference history schema for building consent emails"""

    preference: UserConsentPreference
    privacy_notice_history: PrivacyNoticeHistorySchema


class PrivacyPreferenceHistorySchema(BaseSchema):
    """Schema to represent the snapshot of a saved privacy preference
    This schema is largely for consent reporting.
    """

    id: str
    affected_system_status: Optional[Dict[str, ExecutionLogStatus]]
    preference: UserConsentPreference
    privacy_notice_history: PrivacyNoticeHistorySchema
    privacy_request: Optional[PrivacyRequestResponse]
    relevant_systems: Optional[List[FidesKey]]
    request_origin: Optional[RequestOrigin]
    url_recorded: Optional[str]
    user_agent: Optional[str]
    user_geography: Optional[PrivacyNoticeRegion]


class CurrentPrivacyPreferenceSchema(BaseSchema):
    """Schema to represent the latest saved preference for a given privacy notice
    Note that we return the privacy notice *history* record here though which has the
    contents of the notice the user consented to at the time.
    """

    id: str
    preference: UserConsentPreference
    privacy_notice_history: PrivacyNoticeHistorySchema
    privacy_preference_history_id: str
