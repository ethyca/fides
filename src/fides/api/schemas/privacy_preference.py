from datetime import datetime
from typing import Any, Dict, List, Optional

from fideslang.gvl import (
    GVL_FEATURES,
    GVL_SPECIAL_FEATURES,
    MAPPED_PURPOSES,
    MAPPED_SPECIAL_PURPOSES,
)
from fideslang.validation import FidesKey
from pydantic import Field, conlist, root_validator

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
from fides.api.schemas.tcf import (
    TCFFeatureSave,
    TCFPurposeSave,
    TCFSpecialFeatureSave,
    TCFSpecialPurposeSave,
    TCFVendorSave,
)
from fides.api.util.tcf_util import TCF_COMPONENT_MAPPING, TCFComponentType

# Maps the sections in the request body for saving various TCF preferences
# against the specific database column name on which these preferences are saved
TCF_PREFERENCES_FIELD_MAPPING: Dict[str, str] = {
    "purpose_preferences": TCFComponentType.purpose.value,
    "special_purpose_preferences": TCFComponentType.special_purpose.value,
    "feature_preferences": TCFComponentType.feature.value,
    "special_feature_preferences": TCFComponentType.special_feature.value,
    "vendor_preferences": TCFComponentType.vendor.value,
    "system_preferences": TCFComponentType.system.value,
}


class TCFAttributes(FidesSchema):
    """Common schema for storing values for the relevant TCF Attribute"""

    purpose: Optional[int] = Field(
        title="The TCF purpose that was served or saved against"
    )
    special_purpose: Optional[int] = Field(
        title="The TCF special purpose that was served or saved against"
    )
    vendor: Optional[str] = Field(
        title="The TCF vendor that was served or saved against"
    )
    feature: Optional[int] = Field(
        title="The TCF feature that was served or saved against"
    )
    special_feature: Optional[int] = Field(
        title="The TCF special feature that was served or saved against"
    )
    system: Optional[str] = Field(
        title="The System id that consent was served or saved against. Used when we don't know what vendor "
        "corresponds to the system, so we save preferences against the system directly"
    )


class ConsentOptionCreate(FidesSchema):
    """Schema for saving the user's preference for a given notice"""

    privacy_notice_history_id: str
    preference: UserConsentPreference
    served_notice_history_id: Optional[str]


class PrivacyPreferencesRequest(FidesSchema):
    """Request body for creating PrivacyPreferences.


    "preferences" key reserved for saving preferences against a privacy notice.

    New *_preferences fields are used for saving preferences against various tcf components.
    """

    browser_identity: Identity
    code: Optional[SafeStr]
    preferences: conlist(ConsentOptionCreate, max_items=200) = []  # type: ignore
    purpose_preferences: conlist(TCFPurposeSave, max_items=200) = []  # type: ignore
    special_purpose_preferences: conlist(TCFSpecialPurposeSave, max_items=200) = []  # type: ignore
    vendor_preferences: conlist(TCFVendorSave, max_items=200) = []  # type: ignore
    feature_preferences: conlist(TCFFeatureSave, max_items=200) = []  # type: ignore
    special_feature_preferences: conlist(TCFSpecialFeatureSave, max_items=200) = []  # type: ignore
    system_preferences: conlist(TCFVendorSave, max_items=200) = []  # type: ignore
    policy_key: Optional[FidesKey]  # Will use default consent policy if not supplied
    privacy_experience_id: Optional[SafeStr]
    user_geography: Optional[SafeStr]
    method: Optional[ConsentMethod]

    @root_validator()
    @classmethod
    def validate_tcf_duplicates(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check that there are no duplicates preferences against TCF components
        to avoid confusing responses
        """

        def tcf_duplicates_detected(preference_list: List) -> bool:
            identifiers = [preference.id for preference in preference_list]
            return len(identifiers) != len(set(identifiers))

        for field_name in TCF_PREFERENCES_FIELD_MAPPING:
            if tcf_duplicates_detected(values.get(field_name, [])):
                raise ValueError(
                    f"Duplicate preferences saved against TCF component: '{field_name}'"
                )
        return values


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


class RecordConsentServedRequest(FidesSchema):
    """Request body to use when saving that consent was served"""

    browser_identity: Identity
    code: Optional[SafeStr]  # For verified identity workflow only
    privacy_notice_history_ids: List[SafeStr] = []
    tcf_purposes: List[int] = []
    tcf_special_purposes: List[int] = []
    tcf_vendors: List[SafeStr] = []
    tcf_features: List[int] = []
    tcf_special_features: List[int] = []
    tcf_systems: List[SafeStr] = []
    privacy_experience_id: Optional[SafeStr]
    user_geography: Optional[SafeStr]
    acknowledge_mode: Optional[bool]
    serving_component: ServingComponent

    @root_validator()
    @classmethod
    def validate_tcf_served(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check that TCF values are valid and that there are no duplicates
        """

        def tcf_duplicates_detected(preference_list: List) -> bool:
            return len(preference_list) != len(set(preference_list))

        for field_name in TCF_COMPONENT_MAPPING:
            if tcf_duplicates_detected(values.get(field_name, [])):
                raise ValueError(
                    f"Duplicate served records saved against TCF component: '{field_name}'"
                )

        expected_field_mapping: Dict[str, Dict] = {
            "tcf_purposes": MAPPED_PURPOSES,
            "tcf_special_purposes": MAPPED_SPECIAL_PURPOSES,
            "tcf_features": GVL_FEATURES,
            "tcf_special_features": GVL_SPECIAL_FEATURES,
        }

        for field_name, expected_values in expected_field_mapping.items():
            if not set(values.get(field_name, [])).issubset(
                set(expected_values.keys())
            ):
                raise ValueError(f"Invalid values for {field_name} served.")

        return values


class RecordConsentServedCreate(RecordConsentServedRequest):
    """Schema used on the backend only where we supplement the RecordConsentServedRequest request body
    with information obtained from the request headers and the experience"""

    anonymized_ip_address: Optional[str]
    experience_config_history_id: Optional[SafeStr]
    request_origin: Optional[RequestOrigin]
    url_recorded: Optional[SafeStr]
    user_agent: Optional[SafeStr]


class LastServedConsentSchema(TCFAttributes):
    """Schema that surfaces the the last time a consent item that was shown to a user"""

    id: str
    updated_at: datetime
    served_notice_history_id: str
    privacy_notice_history: Optional[PrivacyNoticeHistorySchema]


class ConsentReportingSchema(TCFAttributes):
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
    privacy_notice_history_id: Optional[str] = Field(
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
    tcf_version: Optional[str] = Field(title="The TCF version where applicable")


class CurrentPrivacyPreferenceSchema(TCFAttributes):
    """Schema to represent the latest saved preference for a given privacy notice
    Note that we return the privacy notice *history* record here though which has the
    contents of the notice the user consented to at the time.
    """

    id: str
    preference: UserConsentPreference
    privacy_notice_history: Optional[PrivacyNoticeHistorySchema]
    privacy_preference_history_id: Optional[str]


class CurrentPrivacyPreferenceReportingSchema(TCFAttributes):
    """Schema to represent the latest saved preference for a given privacy notice
    Note that we return the privacy notice *history* record here though which has the
    contents of the notice the user consented to at the time.
    """

    id: str
    preference: UserConsentPreference
    privacy_notice_history_id: Optional[str]
    privacy_preference_history_id: str
    provided_identity_id: Optional[str]
    created_at: datetime
