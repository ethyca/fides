from datetime import datetime
from typing import Dict, List, Optional

from fideslang.validation import FidesKey
from pydantic import Field, conlist

from fides.api.custom_types import SafeStr
from fides.api.ops.models.policy import ActionType
from fides.api.ops.models.privacy_notice import PrivacyNoticeRegion
from fides.api.ops.models.privacy_preference import RequestOrigin, UserConsentPreference
from fides.api.ops.models.privacy_request import (
    ExecutionLogStatus,
    PrivacyRequestStatus,
)
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


class ConsentReportingSchema(BaseSchema):
    """Schema for consent reporting - largely a join of PrivacyPreferenceHistory and PrivacyRequest"""

    id: str = Field(title="The PrivacyPreferenceHistory id")
    privacy_request_id: Optional[str] = Field(
        title="The Privacy Request id created to propagate preferences"
    )
    email: Optional[str] = Field(title="Email if applicable")
    phone_number: Optional[str] = Field(title="Phone number if applicable")
    fides_user_device_id: Optional[str] = Field(
        title="Fides user device id if applicable"
    )
    secondary_user_ids: Optional[Dict] = Field(title="Other browser identifiers")
    request_timestamp: datetime = Field(
        title="Timestamp when Privacy Preference was saved."
    )
    request_origin: Optional[RequestOrigin] = Field(
        title="Origin of request - privacy center, modal, overlay, API, etc.."
    )
    request_status: Optional[PrivacyRequestStatus] = Field(
        title="Status of the Privacy Request created to propagate preferences."
    )
    request_type: ActionType = Field(title="The Type of Privacy Request.")
    approver_id: Optional[str] = Field(
        title="The username of the user who approved the Privacy Request if applicable"
    )
    privacy_notice_history_id: str = Field(
        title="The id of the specific Privacy Notice History that the user consented to"
    )
    preference: UserConsentPreference = Field(
        title="The user's preference for the given notice: opt_in, opt_out, or acknowledge"
    )
    user_geography: Optional[PrivacyNoticeRegion] = Field(
        title="Detected geography of the user"
    )
    relevant_systems: Optional[List[str]] = Field(
        title="Systems relevant to the given notice by data use.  Note that just because a system is relevant does not mean that a request is necessarily propagated."
    )
    affected_system_status: Dict[str, ExecutionLogStatus] = Field(
        title="Affected system status"
    )
    url_recorded: Optional[str] = Field(
        title="URL of page where preference was recorded"
    )
    user_agent: Optional[str] = Field(title="User agent")


class CurrentPrivacyPreferenceSchema(BaseSchema):
    """Schema to represent the latest saved preference for a given privacy notice
    Note that we return the privacy notice *history* record here though which has the
    contents of the notice the user consented to at the time.
    """

    id: str
    preference: UserConsentPreference
    privacy_notice_history: PrivacyNoticeHistorySchema
    privacy_preference_history_id: str


class CurrentPrivacyPreferenceReportingSchema(BaseSchema):
    """Schema to represent the latest saved preference for a given privacy notice
    Note that we return the privacy notice *history* record here though which has the
    contents of the notice the user consented to at the time.
    """

    id: str
    preference: UserConsentPreference
    privacy_notice_history_id: str
    privacy_preference_history_id: str
    provided_identity_id: Optional[str]
    created_at: datetime
