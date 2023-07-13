from datetime import datetime
from typing import Dict, List, Optional

from fideslang.validation import FidesKey
from pydantic import Field, conlist

from fides.api.custom_types import SafeStr
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.privacy_preference import (
    ConsentMethod,
    RequestOrigin,
    ServingComponent,
)
from fides.api.models.privacy_request import ExecutionLogStatus, PrivacyRequestStatus
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_notice import PrivacyNoticeHistorySchema
from fides.api.schemas.redis_cache import Identity


class ConsentOptionCreate(FidesSchema):
    """Schema for saving the user's preference for a given notice"""

    privacy_notice_history_id: str
    preference: UserConsentPreference
    served_notice_history_id: Optional[str]


class PrivacyPreferencesRequest(FidesSchema):
    """Request body for creating PrivacyPreferences."""

    browser_identity: Identity
    code: Optional[SafeStr]
    preferences: conlist(ConsentOptionCreate, max_items=50)  # type: ignore
    policy_key: Optional[FidesKey]  # Will use default consent policy if not supplied
    privacy_experience_id: Optional[SafeStr]
    user_geography: Optional[SafeStr]
    method: Optional[ConsentMethod]


class PrivacyPreferencesCreate(PrivacyPreferencesRequest):
    """Schema for creating privacy preferences that is supplemented with information
    from the request headers and the experience"""

    anonymized_ip_address: Optional[str]
    experience_config_history_id: Optional[SafeStr]
    request_origin: Optional[RequestOrigin]
    url_recorded: Optional[SafeStr]
    user_agent: Optional[SafeStr]


class MinimalPrivacyPreferenceHistorySchema(FidesSchema):
    """Minimal privacy preference history schema for building consent emails"""

    preference: UserConsentPreference
    privacy_notice_history: PrivacyNoticeHistorySchema


class NoticesServedRequest(FidesSchema):
    """Request body when indicating that notices were served in the UI"""

    browser_identity: Identity
    code: Optional[SafeStr]  # For verified identity workflow only
    privacy_notice_history_ids: List[SafeStr]
    privacy_experience_id: Optional[SafeStr]
    user_geography: Optional[SafeStr]
    acknowledge_mode: Optional[bool]
    serving_component: ServingComponent


class NoticesServedCreate(NoticesServedRequest):
    """Schema used on the backend only where we supplement the NoticesServedRequest request body
    with information obtained from the request headers and the experience"""

    anonymized_ip_address: Optional[str]
    experience_config_history_id: Optional[SafeStr]
    request_origin: Optional[RequestOrigin]
    url_recorded: Optional[SafeStr]
    user_agent: Optional[SafeStr]


class LastServedNoticeSchema(FidesSchema):
    """Schema that surfaces the last version of a notice that was shown to a user"""

    id: str
    updated_at: datetime
    privacy_notice_history: PrivacyNoticeHistorySchema
    served_notice_history_id: str


class ConsentReportingSchema(FidesSchema):
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
    user_geography: Optional[SafeStr] = Field(title="Detected geography of the user")
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
    experience_config_history_id: Optional[str] = Field(
        title="The historical config for the experience that the user was presented - contains the experience language"
    )
    privacy_experience_id: Optional[str] = Field(
        title="The id of the experience that the user was presented - contains the experience type and region"
    )
    truncated_ip_address: Optional[str] = Field(title="Truncated ip address")
    method: Optional[ConsentMethod] = Field(title="Method of consent preference")
    served_notice_history_id: Optional[str] = Field(
        title="The id of the record where the notice was served to the end user"
    )


class CurrentPrivacyPreferenceSchema(FidesSchema):
    """Schema to represent the latest saved preference for a given privacy notice
    Note that we return the privacy notice *history* record here though which has the
    contents of the notice the user consented to at the time.
    """

    id: str
    preference: UserConsentPreference
    privacy_notice_history: PrivacyNoticeHistorySchema
    privacy_preference_history_id: str


class CurrentPrivacyPreferenceReportingSchema(FidesSchema):
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
