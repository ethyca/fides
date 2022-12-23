from datetime import datetime
from enum import Enum as EnumType
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, validator

from fides.api.ops.models.policy import ActionType
from fides.api.ops.models.privacy_request import (
    CheckpointActionRequired,
    ExecutionLogStatus,
    PrivacyRequestStatus,
)
from fides.api.ops.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.ops.schemas.base_class import BaseSchema
from fides.api.ops.schemas.policy import PolicyResponse as PolicySchema
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.util.encryption.aes_gcm_encryption_scheme import (
    verify_encryption_key,
)
from fides.core.config import get_config
from fides.lib.models.audit_log import AuditLogAction
from fides.lib.oauth.schemas.user import PrivacyRequestReviewer

CONFIG = get_config()


class PrivacyRequestDRPStatus(EnumType):
    """A list of privacy request statuses specified by the Data Rights Protocol."""

    open = "open"
    in_progress = "in_progress"
    fulfilled = "fulfilled"
    revoked = "revoked"
    denied = "denied"
    expired = "expired"


class PrivacyRequestDRPStatusResponse(BaseSchema):
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


class PrivacyRequestCreate(BaseSchema):
    """Data required to create a PrivacyRequest"""

    external_id: Optional[str]
    started_processing_at: Optional[datetime]
    finished_processing_at: Optional[datetime]
    requested_at: Optional[datetime]
    identity: Identity
    policy_key: FidesOpsKey
    encryption_key: Optional[str] = None

    @validator("encryption_key")
    def validate_encryption_key(
        cls: "PrivacyRequestCreate", value: Optional[str] = None
    ) -> Optional[str]:
        """Validate encryption key where applicable"""
        if value:
            verify_encryption_key(value.encode(CONFIG.security.encoding))
        return value


class FieldsAffectedResponse(BaseSchema):
    """Schema detailing the individual fields affected by a particular query detailed in the ExecutionLog"""

    path: Optional[str]
    field_name: Optional[str]
    data_categories: Optional[List[str]]

    class Config:
        """Set orm_mode and use_enum_values"""

        orm_mode = True
        use_enum_values = True


class ExecutionLogResponse(BaseSchema):
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


class ExecutionLogDetailResponse(ExecutionLogResponse):
    """Schema for the detailed ExecutionLogs when accessed directly"""

    dataset_name: Optional[str]


class ExecutionAndAuditLogResponse(BaseSchema):
    """Schema for the combined ExecutionLogs and Audit Logs
    associated with a PrivacyRequest"""

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


class RowCountRequest(BaseSchema):
    """Schema for a user to manually confirm data erased for a collection"""

    row_count: int


class CheckpointActionRequiredDetails(CheckpointActionRequired):
    collection: Optional[str] = None  # type: ignore


class VerificationCode(BaseSchema):
    """Request Body for the user to supply their identity verification code"""

    code: str


class ManualWebhookData(BaseSchema):
    checked: bool  # If we have record the user saved data for this webhook (even if it was empty)
    fields: Dict[str, Any]


class PrivacyRequestNotificationInfo(BaseSchema):
    email_addresses: List[str]
    notify_after_failures: int


class PrivacyRequestResponse(BaseSchema):
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
    identity: Optional[Dict[str, Optional[str]]]
    policy: PolicySchema
    action_required_details: Optional[CheckpointActionRequiredDetails] = None
    resume_endpoint: Optional[str]
    days_left: Optional[int]

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


class ReviewPrivacyRequestIds(BaseSchema):
    """Pass in a list of privacy request ids"""

    request_ids: List[str] = Field(..., max_items=50)


class DenyPrivacyRequests(ReviewPrivacyRequestIds):
    """Pass in a list of privacy request ids and rejection reason"""

    reason: Optional[str]


class BulkPostPrivacyRequests(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create of PrivacyRequest responses."""

    succeeded: List[PrivacyRequestResponse]
    failed: List[BulkUpdateFailed]


class BulkReviewResponse(BulkPostPrivacyRequests):
    """Schema with mixed success/failure responses for Bulk Approve/Deny of PrivacyRequest responses."""


class Consent(BaseSchema):
    """Schema for consent."""

    data_use: str
    data_use_description: Optional[str] = None
    opt_in: bool


class ConsentPreferences(BaseSchema):
    """Schema for consent prefernces."""

    consent: Optional[List[Consent]] = None


class ConsentPreferencesWithVerificationCode(BaseSchema):
    """Schema for consent preferences including the verification code."""

    code: Optional[str]
    consent: List[Consent]


class ConsentRequestResponse(BaseSchema):
    """Schema for consent request response."""

    consent_request_id: str


class ConsentRequestVerification(BaseSchema):
    """Schema for consent requests."""

    identity: Identity
    data_use: str
    data_use_description: Optional[str] = None
    opt_in: bool
