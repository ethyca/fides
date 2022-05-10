from datetime import datetime
from enum import Enum as EnumType
from typing import List, Optional, Dict

from pydantic import Field, validator

from fidesops.core.config import config
from fidesops.models.policy import ActionType
from fidesops.schemas.api import BulkResponse, BulkUpdateFailed
from fidesops.schemas.policy import Policy as PolicySchema
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.schemas.base_class import BaseSchema
from fidesops.schemas.shared_schemas import FidesOpsKey
from fidesops.schemas.user import PrivacyRequestReviewer
from fidesops.models.privacy_request import PrivacyRequestStatus, ExecutionLogStatus
from fidesops.util.encryption.aes_gcm_encryption_scheme import verify_encryption_key


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
    identity: PrivacyRequestIdentity
    policy_key: FidesOpsKey
    encryption_key: Optional[str] = None

    @validator("encryption_key")
    def validate_encryption_key(
        cls: "PrivacyRequestCreate", value: Optional[str] = None
    ) -> Optional[str]:
        """Validate encryption key where applicable"""
        if value:
            verify_encryption_key(value.encode(config.security.ENCODING))
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


class PrivacyRequestResponse(BaseSchema):
    """Schema to check the status of a PrivacyRequest"""

    id: str
    created_at: Optional[datetime]
    started_processing_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    reviewer: Optional[PrivacyRequestReviewer]
    finished_processing_at: Optional[datetime]
    status: PrivacyRequestStatus
    external_id: Optional[str]
    # This field intentionally doesn't use the PrivacyRequestIdentity schema
    # as it is an API response field, and we don't want to reveal any more
    # about our PII structure than is explicitly stored in the cache on request
    # creation.
    identity: Optional[Dict[str, str]]
    policy: PolicySchema

    class Config:
        """Set orm_mode and use_enum_values"""

        orm_mode = True
        use_enum_values = True


class PrivacyRequestVerboseResponse(PrivacyRequestResponse):
    """The schema for the more detailed PrivacyRequest response containing detailed execution logs."""

    execution_logs_by_dataset: Dict[str, List[ExecutionLogResponse]] = Field(
        alias="results"
    )

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
