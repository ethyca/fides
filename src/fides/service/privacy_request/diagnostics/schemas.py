"""
Pydantic schemas for the "Privacy Request Diagnostics Export" feature.

IMPORTANT: These diagnostics schemas must **never** include PII. If a column can contain
PII (even optionally / depending on deployment), it should be excluded here.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PrivacyRequestSnapshot(BaseModel):
    """
    Diagnostics projection of a single `privacyrequest` row.

    This model intentionally contains **non-PII fields only**.
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: str
    status: str

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    requested_at: Optional[datetime] = None
    started_processing_at: Optional[datetime] = None
    finished_processing_at: Optional[datetime] = None

    reviewed_at: Optional[datetime] = None
    finalized_at: Optional[datetime] = None

    policy_id: Optional[str] = None
    property_id: Optional[str] = None

    canceled_at: Optional[datetime] = None

    deleted_at: Optional[datetime] = None


class ProvidedIdentitySnapshot(BaseModel):
    """
    Diagnostics projection of a single `providedidentity` row.

    Non-PII only: excludes encrypted identity values and hashed identity values.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    field_name: str
    field_label: Optional[str] = None

    encrypted_value_present: bool
    hashed_value_present: bool
    is_hash_migrated: Optional[bool] = None


class ExecutionLogSnapshot(BaseModel):
    """
    Diagnostics projection of a single `executionlog` row.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    status: str
    action_type: str
    message: Optional[str] = None

    connection_key: Optional[str] = None
    dataset_name: Optional[str] = None
    collection_name: Optional[str] = None

    fields_affected_count: Optional[int] = None


class AuditLogSnapshot(BaseModel):
    """
    Diagnostics projection of a single `auditlog` row.

    Non-PII only: excludes `message` (free text) and `user_id` (operator identifier).
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    action: str


class RequestTaskSnapshot(BaseModel):
    """
    Diagnostics projection of a single `requesttask` row.

    Non-PII only: excludes any access/erasure payloads and other large JSON blobs.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    status: str
    action_type: str

    privacy_request_id: Optional[str] = None

    collection_address: str
    dataset_name: str
    collection_name: str

    async_type: Optional[str] = None
    callback_succeeded: Optional[bool] = None
    rows_masked: Optional[int] = None
    consent_sent: Optional[bool] = None

    upstream_tasks: Optional[List[str]] = None
    downstream_tasks: Optional[List[str]] = None
    all_descendant_tasks: Optional[List[str]] = None


class AttachmentSnapshot(BaseModel):
    """
    Diagnostics projection of a single `attachment` row.

    Non-PII only: excludes `file_name`, `user_id`, and any download URLs / file contents.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    attachment_type: str
    storage_key: str


class AttachmentReferenceSnapshot(BaseModel):
    """
    Diagnostics projection of a single `attachment_reference` row.

    Non-PII only: these are internal IDs + reference type.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None

    attachment_id: str
    reference_id: str
    reference_type: str


class CommentSnapshot(BaseModel):
    """
    Diagnostics projection of a single `comment` row.

    Non-PII only: excludes `comment_text` (free text) and `user_id` (operator identifier).
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    comment_type: str


class CommentReferenceSnapshot(BaseModel):
    """
    Diagnostics projection of a single `comment_reference` row.

    Non-PII only: internal IDs + reference type.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None

    comment_id: str
    reference_id: str
    reference_type: str


class PrivacyRequestErrorSnapshot(BaseModel):
    """
    Diagnostics projection of a single `privacyrequesterror` row.

    Non-PII only: this table is just tracking email/message dispatch state.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    message_sent: bool


class CustomPrivacyRequestFieldSnapshot(BaseModel):
    """
    Diagnostics projection of a single `custom_privacy_request_field` row.

    Non-PII only: excludes encrypted values and hashes; includes only metadata and presence flags.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    field_name: str
    field_label: str

    encrypted_value_present: bool
    hashed_value_present: bool
    is_hash_migrated: Optional[bool] = None


class RequestTaskSubRequestSnapshot(BaseModel):
    """
    Diagnostics projection of a single `request_task_sub_request` row.

    Non-PII only: excludes param values and access data payloads.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    request_task_id: str
    status: str
    rows_masked: Optional[int] = None


class StorageConfigSnapshot(BaseModel):
    """
    Diagnostics projection of a single `storageconfig` row.

    Non-PII only: excludes `details` and `secrets`.
    """

    model_config = ConfigDict(extra="forbid")

    key: str
    name: Optional[str] = None
    type: str
    format: Optional[str] = None
    is_default: bool


class DatasetConfigSnapshot(BaseModel):
    """
    Diagnostics projection of a single `datasetconfig` row.

    Non-PII only: includes identifiers and linkage to CTL dataset.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    fides_key: str
    connection_config_id: str
    ctl_dataset_id: str


class CtlDatasetSnapshot(BaseModel):
    """
    Diagnostics projection of a single CTL `ctl_datasets` row.

    Non-PII only: excludes full dataset JSON (collections/meta).
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    fides_key: str
    name: Optional[str] = None


class MessagingConfigSnapshot(BaseModel):
    """
    Diagnostics projection of a single `messagingconfig` row.

    Non-PII only: excludes `details` and `secrets`.
    """

    model_config = ConfigDict(extra="forbid")

    key: str
    name: Optional[str] = None
    service_type: str
    last_test_timestamp: Optional[datetime] = None
    last_test_succeeded: Optional[bool] = None


class ManualTaskSnapshot(BaseModel):
    """
    Diagnostics projection of a single `manual_task` row.

    Non-PII only: excludes assigned user references.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    task_type: str
    parent_entity_id: str
    parent_entity_type: str


class ManualTaskInstanceSnapshot(BaseModel):
    """
    Diagnostics projection of a single `manual_task_instance` row.

    Non-PII only: excludes `completed_by_id`.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    task_id: Optional[str] = None
    config_id: str

    entity_id: str
    entity_type: str

    status: str
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None


class ManualTaskConfigSnapshot(BaseModel):
    """Diagnostics projection of a single `manual_task_config` row (metadata only)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    task_id: Optional[str] = None
    config_type: str
    version: int
    is_current: bool
    execution_timing: str


class ManualTaskConfigFieldSnapshot(BaseModel):
    """
    Diagnostics projection of a single `manual_task_config_field` row.

    Non-PII only: excludes `field_metadata` contents.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    task_id: Optional[str] = None
    config_id: str
    field_key: str
    field_type: str
    execution_timing: Optional[str] = None


class ManualTaskReferenceSnapshot(BaseModel):
    """
    Diagnostics projection of a single `manual_task_reference` row.

    Non-PII only: assigned user reference IDs are omitted.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    task_id: str
    reference_type: str
    reference_id: Optional[str] = None
    config_field_key: Optional[str] = None


class ManualTaskSubmissionSnapshot(BaseModel):
    """
    Diagnostics projection of a single `manual_task_submission` row.

    Non-PII only: excludes `data` and `submitted_by`.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    task_id: Optional[str] = None
    config_id: str
    field_id: str
    instance_id: str

    submitted_at: datetime


class ManualTaskConditionalDependencySnapshot(BaseModel):
    """
    Diagnostics projection of a single `manual_task_conditional_dependency` row.

    Non-PII only: excludes condition tree contents.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    manual_task_id: str
    config_field_key: Optional[str] = None


class PrivacyRequestDiagnostics(BaseModel):
    """Top-level diagnostics export model (non-PII only)."""

    model_config = ConfigDict(extra="forbid")

    privacy_request: PrivacyRequestSnapshot
    privacy_request_error: Optional[PrivacyRequestErrorSnapshot] = None
    custom_privacy_request_fields: List[CustomPrivacyRequestFieldSnapshot]
    provided_identities: List[ProvidedIdentitySnapshot]
    execution_logs: List[ExecutionLogSnapshot]
    audit_logs: List[AuditLogSnapshot]
    request_tasks: List[RequestTaskSnapshot]
    request_task_sub_requests: List[RequestTaskSubRequestSnapshot]
    dataset_configs: List[DatasetConfigSnapshot]
    ctl_datasets: List[CtlDatasetSnapshot]
    storage_configs: List[StorageConfigSnapshot]
    messaging_config: Optional[MessagingConfigSnapshot] = None
    manual_tasks: List[ManualTaskSnapshot]
    manual_task_instances: List[ManualTaskInstanceSnapshot]
    manual_task_references: List[ManualTaskReferenceSnapshot]
    manual_task_configs: List[ManualTaskConfigSnapshot]
    manual_task_config_fields: List[ManualTaskConfigFieldSnapshot]
    manual_task_submissions: List[ManualTaskSubmissionSnapshot]
    manual_task_conditional_dependencies: List[ManualTaskConditionalDependencySnapshot]
    attachments: List[AttachmentSnapshot]
    attachment_references: List[AttachmentReferenceSnapshot]
    comments: List[CommentSnapshot]
    comment_references: List[CommentReferenceSnapshot]


class PrivacyRequestDiagnosticsExportResponse(BaseModel):
    """Response payload for a diagnostics export request."""

    model_config = ConfigDict(extra="forbid")

    download_url: str
    storage_type: str
    object_key: str
    created_at: datetime
