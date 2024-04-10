from datetime import datetime
from enum import Enum as EnumType
from typing import Any, Dict, List, Optional, Type, Union

from fideslang.validation import FidesKey
from pydantic import Field, validator

from fides.api.custom_types import SafeStr
from fides.api.models.audit_log import AuditLogAction
from fides.api.models.privacy_request import (
    CheckpointActionRequired,
    ExecutionLogStatus,
    PrivacyRequestStatus,
)
from fides.api.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.policy import ActionType
from fides.api.schemas.policy import PolicyResponse as PolicySchema
from fides.api.schemas.redis_cache import CustomPrivacyRequestField, Identity
from fides.api.schemas.user import PrivacyRequestReviewer
from fides.api.util.encryption.aes_gcm_encryption_scheme import verify_encryption_key
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
    expected_by: Optional[datetime]
    processing_details: Optional[str]
    status: PrivacyRequestDRPStatus
    reason: Optional[str]
    user_verification_url: Optional[str]

    class Config:
        """Set orm_mode and use_enum_values"""

        orm_mode = True
        use_enum_values = True


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

    external_id: Optional[str]
    started_processing_at: Optional[datetime]
    finished_processing_at: Optional[datetime]
    requested_at: Optional[datetime]
    identity: Identity
    consent_request_id: Optional[str] = None
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]] = None
    policy_key: FidesKey
    encryption_key: Optional[str] = None
    consent_preferences: Optional[List[Consent]] = None  # TODO Slated for deprecation

    @validator("encryption_key")
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


class FieldsAffectedResponse(FidesSchema):
    """Schema detailing the individual fields affected by a particular query detailed in the ExecutionLog"""

    path: Optional[str]
    field_name: Optional[str]
    data_categories: Optional[List[str]]

    class Config:
        """Set orm_mode and use_enum_values"""

        orm_mode = True
        use_enum_values = True


class ExecutionLogResponse(FidesSchema):
    """Schema for the embedded ExecutionLogs associated with a PrivacyRequest"""

    collection_name: Optional[str]
    fields_affected: Optional[List[FieldsAffectedResponse]]
    message: Optional[str]
    action_type: ActionType
    status: ExecutionLogStatus
    updated_at: Optional[datetime]

    class Config:
        """Set orm_mode and use_enum_values"""

        orm_mode = True
        use_enum_values = True


class PrivacyRequestTaskSchema(FidesSchema):
    """Schema for Privacy Request Tasks, which are individual nodes that are queued"""

    id: str
    collection_address: str
    status: ExecutionLogStatus
    created_at: datetime
    updated_at: datetime
    upstream_tasks: List[str]
    downstream_tasks: List[str]
    action_type: ActionType


class ExecutionLogDetailResponse(ExecutionLogResponse):
    """Schema for the detailed ExecutionLogs when accessed directly"""

    connection_key: Optional[str]
    dataset_name: Optional[str]


class ExecutionAndAuditLogResponse(FidesSchema):
    """Schema for the combined ExecutionLogs and Audit Logs
    associated with a PrivacyRequest"""

    connection_key: Optional[str]
    collection_name: Optional[str]
    fields_affected: Optional[List[FieldsAffectedResponse]]
    message: Optional[str]
    action_type: Optional[ActionType]
    status: Optional[Union[ExecutionLogStatus, AuditLogAction]]
    updated_at: Optional[datetime]
    user_id: Optional[str]

    class Config:
        """Set orm_mode and allow population by field name"""

        use_enum_values = True
        allow_population_by_field_name = True


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
    created_at: Optional[datetime]
    started_processing_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    reviewer: Optional[PrivacyRequestReviewer]
    finished_processing_at: Optional[datetime]
    identity_verified_at: Optional[datetime]
    paused_at: Optional[datetime]
    status: PrivacyRequestStatus
    external_id: Optional[str]
    # This field intentionally doesn't use the Identity schema
    # as it is an API response field, and we don't want to reveal any more
    # about our PII structure than is explicitly stored in the cache on request
    # creation.
    identity: Optional[Dict[str, Union[Optional[str], Dict[str, Any]]]]
    custom_privacy_request_fields: Optional[Dict[str, Any]]
    policy: PolicySchema
    action_required_details: Optional[CheckpointActionRequiredDetails] = None
    resume_endpoint: Optional[str]
    days_left: Optional[int]
    custom_privacy_request_fields_approved_by: Optional[str]
    custom_privacy_request_fields_approved_at: Optional[datetime]

    class Config:
        """Set orm_mode and use_enum_values"""

        orm_mode = True
        use_enum_values = True


class PrivacyRequestVerboseResponse(PrivacyRequestResponse):
    """The schema for the more detailed PrivacyRequest response containing both
    detailed execution logs and audit logs."""

    execution_and_audit_logs_by_dataset: Dict[
        str, List[ExecutionAndAuditLogResponse]
    ] = Field(alias="results")

    class Config:
        """Allow the results field to be populated by the 'PrivacyRequest.execution_logs_by_dataset' property"""

        allow_population_by_field_name = True


class ReviewPrivacyRequestIds(FidesSchema):
    """Pass in a list of privacy request ids"""

    request_ids: List[str] = Field(..., max_items=50)


class DenyPrivacyRequests(ReviewPrivacyRequestIds):
    """Pass in a list of privacy request ids and rejection reason"""

    reason: Optional[SafeStr]


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

    code: Optional[str]
    consent: List[Consent]
    policy_key: Optional[FidesKey] = None
    executable_options: Optional[List[ConsentWithExecutableStatus]]
    browser_identity: Optional[Identity]


class ConsentRequestResponse(FidesSchema):
    """Schema for consent request response."""

    consent_request_id: str


class ConsentRequestVerification(FidesSchema):
    """Schema for consent requests."""

    identity: Identity
    data_use: str
    data_use_description: Optional[str] = None
    opt_in: bool
