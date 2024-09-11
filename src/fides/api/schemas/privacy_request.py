from datetime import datetime
from enum import Enum as EnumType
from typing import Any, Dict, List, Optional, Type, Union

from fideslang.validation import FidesKey
from pydantic import ConfigDict, Field, field_serializer, field_validator

from fides.api.custom_types import SafeStr
from fides.api.models.audit_log import AuditLogAction
from fides.api.models.privacy_request import (
    CheckpointActionRequired,
    ExecutionLogStatus,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.api.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.policy import ActionType
from fides.api.schemas.policy import PolicyResponse as PolicySchema
from fides.api.schemas.redis_cache import CustomPrivacyRequestField, Identity
from fides.api.schemas.user import PrivacyRequestReviewer
from fides.api.util.collection_util import Row
from fides.api.util.encryption.aes_gcm_encryption_scheme import verify_encryption_key
from fides.api.util.enums import ColumnSort
from fides.config import CONFIG


class PrivacyRequestDRPStatus(EnumType):
    """A list of privacy request statuses specified by the Data Rights Protocol."""

    open = "open"
    in_progress = "in_progress"
    fulfilled = "fulfilled"
    revoked = "revoked"
    denied = "denied"
    expired = "expired"


class PrivacyRequestDRPStatusResponse(FidesSchema):
    """A Fidesops PrivacyRequest updated to fit the Data Rights Protocol specification."""

    request_id: str
    received_at: datetime
    expected_by: Optional[datetime] = None
    processing_details: Optional[str] = None
    status: PrivacyRequestDRPStatus
    reason: Optional[str] = None
    user_verification_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class Consent(FidesSchema):
    """
    Deprecated: This used to be populated and sent to the server by a `config.json` in the UI
    """

    data_use: str
    data_use_description: Optional[str] = None
    opt_in: bool
    has_gpc_flag: bool = False
    conflicts_with_gpc: bool = False


class ConsentReport(Consent):
    """
    Keeps record of each of the preferences that have been recorded via ConsentReporting endpoints.
    """

    id: str
    identity: Identity
    created_at: datetime
    updated_at: datetime


class PrivacyRequestCreate(FidesSchema):
    """Data required to create a PrivacyRequest"""

    external_id: Optional[str] = None
    started_processing_at: Optional[datetime] = None
    finished_processing_at: Optional[datetime] = None
    requested_at: Optional[datetime] = None
    identity: Identity
    consent_request_id: Optional[str] = None
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None
    policy_key: FidesKey
    encryption_key: Optional[str] = None
    property_id: Optional[str] = None
    consent_preferences: Optional[List[Consent]] = None  # TODO Slated for deprecation
    source: Optional[PrivacyRequestSource] = None

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(
        cls: Type["PrivacyRequestCreate"], value: Optional[str] = None
    ) -> Optional[str]:
        """Validate encryption key where applicable"""
        if value:
            verify_encryption_key(value.encode(CONFIG.security.encoding))
        return value


class ConsentRequestCreate(FidesSchema):
    """Data required to create a consent PrivacyRequest"""

    identity: Identity
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None
    property_id: Optional[str] = None
    source: Optional[PrivacyRequestSource] = None


class FieldsAffectedResponse(FidesSchema):
    """Schema detailing the individual fields affected by a particular query detailed in the ExecutionLog"""

    path: Optional[str]
    field_name: Optional[str]
    data_categories: Optional[List[str]]
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ExecutionLogStatusSerializeOverride(FidesSchema):
    """Override to serialize "paused" Execution Logs as awaiting_processing instead"""

    status: ExecutionLogStatus
    model_config = ConfigDict(from_attributes=True, use_enum_values=False)

    @field_serializer("status")
    def serialize_status(self, status: ExecutionLogStatus) -> str:
        """For statuses, we want to use the name instead of the value
        This is for backwards compatibility where we are repurposing the "paused" status
        to read "awaiting processing"
        """
        return status.name


class ExecutionLogResponse(ExecutionLogStatusSerializeOverride):
    """Schema for the embedded ExecutionLogs associated with a PrivacyRequest"""

    collection_name: Optional[str] = None
    fields_affected: Optional[List[FieldsAffectedResponse]] = None
    message: Optional[str] = None
    action_type: ActionType
    updated_at: Optional[datetime] = None


class PrivacyRequestTaskSchema(ExecutionLogStatusSerializeOverride):
    """Schema for Privacy Request Tasks, which are individual nodes that are queued"""

    id: str
    collection_address: str
    created_at: datetime
    updated_at: datetime
    upstream_tasks: List[str]
    downstream_tasks: List[str]
    action_type: ActionType


class ExecutionLogDetailResponse(ExecutionLogResponse):
    """Schema for the detailed ExecutionLogs when accessed directly"""

    connection_key: Optional[str] = None
    dataset_name: Optional[str] = None


class ExecutionAndAuditLogResponse(FidesSchema):
    """Schema for the combined ExecutionLogs and Audit Logs
    associated with a PrivacyRequest"""

    connection_key: Optional[str] = None
    collection_name: Optional[str] = None
    fields_affected: Optional[List[FieldsAffectedResponse]] = None
    message: Optional[str] = None
    action_type: Optional[ActionType] = None
    status: Optional[Union[ExecutionLogStatus, AuditLogAction, str]] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)

    @field_serializer("status")
    def serialize_status(
        self, status: Optional[Union[ExecutionLogStatus, AuditLogAction, str]]
    ) -> Optional[str]:
        """For statuses, we want to use the name instead of the value
        This is for backwards compatibility where we are repurposing the "paused" status
        to read "awaiting processing"

        Generally, status will be a string here because we had to convert both ExecutionLogStatuses
        and AuditLogAction statuses to strings so we could union both resources into the same query
        """
        if isinstance(status, (AuditLogAction, ExecutionLogStatus)):
            return status.name if status else None

        return "awaiting_processing" if status == "paused" else status


class RowCountRequest(FidesSchema):
    """Schema for a user to manually confirm data erased for a collection"""

    row_count: int


class CheckpointActionRequiredDetails(CheckpointActionRequired):
    collection: Optional[str] = None  # type: ignore


class VerificationCode(FidesSchema):
    """Request Body for the user to supply their identity verification code"""

    code: str


class ManualWebhookData(FidesSchema):
    checked: bool  # If we have record the user saved data for this webhook (even if it was empty)
    fields: Dict[str, Any]


class PrivacyRequestNotificationInfo(FidesSchema):
    email_addresses: List[str]
    notify_after_failures: int


class PrivacyRequestResponse(FidesSchema):
    """Schema to check the status of a PrivacyRequest"""

    id: str
    created_at: Optional[datetime] = None
    started_processing_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewer: Optional[PrivacyRequestReviewer] = None
    finished_processing_at: Optional[datetime] = None
    identity_verified_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    status: PrivacyRequestStatus
    external_id: Optional[str] = None
    # This field intentionally doesn't use the Identity schema
    # as it is an API response field, and we don't want to reveal any more
    # about our PII structure than is explicitly stored in the cache on request
    # creation.
    identity: Optional[Dict[str, Union[Optional[str], Dict[str, Any]]]] = None
    custom_privacy_request_fields: Optional[Dict[str, Any]] = None
    policy: PolicySchema
    action_required_details: Optional[CheckpointActionRequiredDetails] = None
    resume_endpoint: Optional[str] = None
    days_left: Optional[int] = None
    custom_privacy_request_fields_approved_by: Optional[str] = None
    custom_privacy_request_fields_approved_at: Optional[datetime] = None
    source: Optional[PrivacyRequestSource] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class PrivacyRequestVerboseResponse(PrivacyRequestResponse):
    """The schema for the more detailed PrivacyRequest response containing both
    detailed execution logs and audit logs."""

    execution_and_audit_logs_by_dataset: Dict[
        str, List[ExecutionAndAuditLogResponse]
    ] = Field(alias="results")
    model_config = ConfigDict(populate_by_name=True)


class ReviewPrivacyRequestIds(FidesSchema):
    """Pass in a list of privacy request ids"""

    request_ids: List[str] = Field(..., max_length=50)


class DenyPrivacyRequests(ReviewPrivacyRequestIds):
    """Pass in a list of privacy request ids and rejection reason"""

    reason: Optional[SafeStr] = None


class BulkPostPrivacyRequests(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create of PrivacyRequest responses."""

    succeeded: List[PrivacyRequestResponse]
    failed: List[BulkUpdateFailed]


class BulkReviewResponse(BulkPostPrivacyRequests):
    """Schema with mixed success/failure responses for Bulk Approve/Deny of PrivacyRequest responses."""


class ConsentPreferences(FidesSchema):
    """Schema for consent preferences."""

    consent: Optional[List[Consent]] = None


class ConsentWithExecutableStatus(FidesSchema):
    """Schema for executable consents"""

    data_use: str
    executable: bool


class ConsentPreferencesWithVerificationCode(FidesSchema):
    """Schema for consent preferences including the verification code."""

    code: Optional[str] = None
    consent: List[Consent]
    policy_key: Optional[FidesKey] = None
    executable_options: Optional[List[ConsentWithExecutableStatus]] = None
    browser_identity: Optional[Identity] = None


class ConsentRequestResponse(FidesSchema):
    """Schema for consent request response."""

    consent_request_id: str


class ConsentRequestVerification(FidesSchema):
    """Schema for consent requests."""

    identity: Identity
    data_use: str
    data_use_description: Optional[str] = None
    opt_in: bool


class RequestTaskCallbackRequest(FidesSchema):
    """Request body for Async Callback"""

    access_results: Optional[List[Row]] = Field(
        default=None,
        description="Access results collected asynchronously, as a list of rows.  Use caution; this data may be used by dependent tasks downstream and/or uploaded to the end user.",
    )
    rows_masked: Optional[int] = Field(
        default=None, description="Number of records masked, as an integer"
    )


class PrivacyRequestFilter(FidesSchema):
    request_id: Optional[str] = None
    identities: Optional[Dict[str, Any]] = Field(
        None, examples=[{"email": "user@example.com", "loyalty_id": "CH-1"}]
    )
    fuzzy_search_str: Optional[str] = (
        None  # catch-all for any strings we want to fuzzy-search privacy requests on. Currently only applies to identities and privacy request ids
    )
    custom_privacy_request_fields: Optional[Dict[str, Any]] = Field(
        None, examples=[{"site_id": "abc", "subscriber_id": "123"}]
    )
    status: Optional[Union[PrivacyRequestStatus, List[PrivacyRequestStatus]]] = None
    created_lt: Optional[datetime] = None
    created_gt: Optional[datetime] = None
    started_lt: Optional[datetime] = None
    started_gt: Optional[datetime] = None
    completed_lt: Optional[datetime] = None
    completed_gt: Optional[datetime] = None
    errored_lt: Optional[datetime] = None
    errored_gt: Optional[datetime] = None
    external_id: Optional[str] = None
    action_type: Optional[ActionType] = None
    verbose: Optional[bool] = False
    include_identities: Optional[bool] = False
    include_custom_privacy_request_fields: Optional[bool] = False
    download_csv: Optional[bool] = False
    sort_field: str = "created_at"
    sort_direction: ColumnSort = ColumnSort.DESC

    model_config = ConfigDict(extra="forbid")

    @field_validator("status")
    @classmethod
    def validate_status_field(
        cls,
        field_value: Union[PrivacyRequestStatus, List[PrivacyRequestStatus]],
    ) -> List[PrivacyRequestStatus]:
        """
        Keeps the status field flexible but converts a single value to a list for consistent processing.
        """
        if isinstance(field_value, PrivacyRequestStatus):
            return [field_value]
        return field_value
