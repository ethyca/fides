"""
Models for the "Privacy Request Diagnostics Export" feature.

IMPORTANT: These diagnostics models must **never** include PII. If a column can contain
PII (even optionally / depending on deployment), it should be excluded here.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestNotFound
from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
)
from fides.api.models.audit_log import AuditLog
from fides.api.models.comment import Comment, CommentReference, CommentReferenceType
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.messaging import MessagingConfig
from fides.api.models.privacy_request.execution_log import ExecutionLog
from fides.api.models.privacy_request.provided_identity import ProvidedIdentity
from fides.api.models.privacy_request.privacy_request import (
    PrivacyRequest,
    CustomPrivacyRequestField,
    PrivacyRequestError,
)
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.models.privacy_request.request_task import RequestTaskSubRequest
from fides.api.models.sql_models import Dataset as CtlDataset  # type: ignore[attr-defined]
from fides.api.models.storage import StorageConfig

from fides.api.models.manual_task.conditional_dependency import (
    ManualTaskConditionalDependency,
)
from fides.api.models.manual_task.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskEntityType,
    ManualTaskInstance,
    ManualTaskReference,
    ManualTaskReferenceType,
    ManualTaskSubmission,
)


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


def get_privacy_request_snapshot(
    privacy_request_id: str, db: Session
) -> PrivacyRequestSnapshot:
    """Fetch a `PrivacyRequest` by id and project it into a diagnostics snapshot."""

    # Use query_without_large_columns to avoid loading encrypted access results blobs, etc.
    privacy_request = (
        PrivacyRequest.query_without_large_columns(db)
        .filter(PrivacyRequest.id == privacy_request_id)
        .first()
    )
    if not privacy_request:
        raise PrivacyRequestNotFound(
            f"Privacy request with id {privacy_request_id} not found"
        )

    return PrivacyRequestSnapshot.model_validate(privacy_request)


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


def get_provided_identities(
    privacy_request_id: str, db: Session
) -> List[ProvidedIdentitySnapshot]:
    """Fetch provided identities for a privacy request and project into non-PII snapshots."""

    identities = (
        db.query(ProvidedIdentity)
        .filter(ProvidedIdentity.privacy_request_id == privacy_request_id)
        .order_by(ProvidedIdentity.created_at.asc())
        .all()
    )

    return [
        ProvidedIdentitySnapshot(
            id=identity.id,
            created_at=identity.created_at,
            updated_at=identity.updated_at,
            field_name=identity.field_name,
            field_label=identity.field_label,
            encrypted_value_present=bool(identity.encrypted_value),
            hashed_value_present=bool(identity.hashed_value),
            is_hash_migrated=getattr(identity, "is_hash_migrated", None),
        )
        for identity in identities
    ]


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


def get_execution_logs(
    privacy_request_id: str, db: Session
) -> List[ExecutionLogSnapshot]:
    """Fetch execution logs for a privacy request and project into non-PII snapshots."""

    logs = (
        db.query(ExecutionLog)
        .filter(ExecutionLog.privacy_request_id == privacy_request_id)
        .order_by(ExecutionLog.updated_at.asc())
        .all()
    )

    return [
        ExecutionLogSnapshot(
            id=log.id,
            created_at=log.created_at,
            updated_at=log.updated_at,
            status=getattr(log.status, "value", str(log.status)),
            action_type=getattr(log.action_type, "value", str(log.action_type)),
            message=log.message,
            connection_key=log.connection_key,
            dataset_name=log.dataset_name,
            collection_name=log.collection_name,
            fields_affected_count=len(log.fields_affected) if log.fields_affected else None,
        )
        for log in logs
    ]


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


def get_audit_logs(
    privacy_request_id: str, db: Session
) -> List[AuditLogSnapshot]:
    """Fetch audit logs for a privacy request and project into non-PII snapshots."""

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.privacy_request_id == privacy_request_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    return [
        AuditLogSnapshot(
            id=log.id,
            created_at=log.created_at,
            updated_at=log.updated_at,
            action=getattr(log.action, "value", str(log.action)),
        )
        for log in logs
    ]


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


def get_request_tasks(
    privacy_request_id: str, db: Session
) -> List[RequestTaskSnapshot]:
    """Fetch request tasks for a privacy request and project into non-PII snapshots."""

    query = (
        db.query(RequestTask)
        .filter(RequestTask.privacy_request_id == privacy_request_id)
        .order_by(RequestTask.created_at.asc())
    )
    query = RequestTask.query_with_deferred_data(query)
    tasks = query.all()

    return [
        RequestTaskSnapshot(
            id=task.id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            status=getattr(task.status, "value", str(task.status)),
            action_type=getattr(task.action_type, "value", str(task.action_type)),
            privacy_request_id=task.privacy_request_id,
            collection_address=task.collection_address,
            dataset_name=task.dataset_name,
            collection_name=task.collection_name,
            async_type=getattr(task.async_type, "value", str(task.async_type))
            if task.async_type is not None
            else None,
            callback_succeeded=task.callback_succeeded,
            rows_masked=task.rows_masked,
            consent_sent=task.consent_sent,
            upstream_tasks=list(task.upstream_tasks) if task.upstream_tasks else None,
            downstream_tasks=list(task.downstream_tasks)
            if task.downstream_tasks
            else None,
            all_descendant_tasks=list(task.all_descendant_tasks)
            if task.all_descendant_tasks
            else None,
        )
        for task in tasks
    ]


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


def get_attachments(privacy_request_id: str, db: Session) -> List[AttachmentSnapshot]:
    """Fetch attachments referenced by the privacy request and project into non-PII snapshots."""

    attachments = (
        db.query(Attachment)
        .join(AttachmentReference)
        .filter(
            AttachmentReference.reference_id == privacy_request_id,
            AttachmentReference.reference_type == AttachmentReferenceType.privacy_request,
        )
        .order_by(Attachment.created_at.asc())
        .all()
    )

    return [
        AttachmentSnapshot(
            id=attachment.id,
            created_at=attachment.created_at,
            updated_at=attachment.updated_at,
            attachment_type=getattr(
                attachment.attachment_type, "value", str(attachment.attachment_type)
            ),
            storage_key=attachment.storage_key,
        )
        for attachment in attachments
    ]


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


def get_attachment_references(
    privacy_request_id: str, db: Session
) -> List[AttachmentReferenceSnapshot]:
    """
    Fetch attachment references for attachments associated with this privacy request.

    This includes references beyond the privacy request itself (e.g. comment, manual_task_submission)
    so you can see *where* an attachment came from.
    """

    attachment_ids: List[str] = [
        a.id for a in get_attachments(privacy_request_id, db)  # type: ignore[attr-defined]
    ]
    if not attachment_ids:
        return []

    refs = (
        db.query(AttachmentReference)
        .filter(AttachmentReference.attachment_id.in_(attachment_ids))
        .order_by(AttachmentReference.created_at.asc())
        .all()
    )

    return [
        AttachmentReferenceSnapshot(
            id=ref.id,
            created_at=ref.created_at,
            attachment_id=ref.attachment_id,
            reference_id=ref.reference_id,
            reference_type=getattr(ref.reference_type, "value", str(ref.reference_type)),
        )
        for ref in refs
    ]


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


def get_comments(privacy_request_id: str, db: Session) -> List[CommentSnapshot]:
    """Fetch comments referenced by the privacy request and project into non-PII snapshots."""

    comments = (
        db.query(Comment)
        .join(CommentReference)
        .filter(
            CommentReference.reference_id == privacy_request_id,
            CommentReference.reference_type == CommentReferenceType.privacy_request,
        )
        .order_by(Comment.created_at.asc())
        .all()
    )

    return [
        CommentSnapshot(
            id=comment.id,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            comment_type=getattr(comment.comment_type, "value", str(comment.comment_type)),
        )
        for comment in comments
    ]


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


def get_comment_references(
    privacy_request_id: str, db: Session
) -> List[CommentReferenceSnapshot]:
    """
    Fetch comment references for comments associated with this privacy request.

    This includes references beyond the privacy request itself (e.g. manual_task_submission)
    so you can see *where* comments were attached.
    """

    comment_ids: List[str] = [c.id for c in get_comments(privacy_request_id, db)]
    if not comment_ids:
        return []

    refs = (
        db.query(CommentReference)
        .filter(CommentReference.comment_id.in_(comment_ids))
        .order_by(CommentReference.created_at.asc())
        .all()
    )

    return [
        CommentReferenceSnapshot(
            id=ref.id,
            created_at=ref.created_at,
            comment_id=ref.comment_id,
            reference_id=ref.reference_id,
            reference_type=getattr(ref.reference_type, "value", str(ref.reference_type)),
        )
        for ref in refs
    ]


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


def get_privacy_request_error(
    privacy_request_id: str, db: Session
) -> Optional[PrivacyRequestErrorSnapshot]:
    """Fetch privacy request error row (if any) and project into a non-PII snapshot."""

    pr_error = (
        db.query(PrivacyRequestError)
        .filter(PrivacyRequestError.privacy_request_id == privacy_request_id)
        .one_or_none()
    )
    if not pr_error:
        return None

    return PrivacyRequestErrorSnapshot(
        id=pr_error.id,
        created_at=pr_error.created_at,
        updated_at=pr_error.updated_at,
        message_sent=bool(pr_error.message_sent),
    )


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


def get_custom_privacy_request_fields(
    privacy_request_id: str, db: Session
) -> List[CustomPrivacyRequestFieldSnapshot]:
    """Fetch custom privacy request fields and project into non-PII snapshots."""

    rows = (
        db.query(
            CustomPrivacyRequestField.id,
            CustomPrivacyRequestField.created_at,
            CustomPrivacyRequestField.updated_at,
            CustomPrivacyRequestField.field_name,
            CustomPrivacyRequestField.field_label,
            CustomPrivacyRequestField.hashed_value,
            CustomPrivacyRequestField.encrypted_value,
            CustomPrivacyRequestField.is_hash_migrated,  # type: ignore[attr-defined]
        )
        .filter(CustomPrivacyRequestField.privacy_request_id == privacy_request_id)
        .order_by(CustomPrivacyRequestField.created_at.asc())
        .all()
    )

    # NOTE: We intentionally do not surface any values/hashes. Presence checks still touch the column,
    # but do not include its contents in the export.
    return [
        CustomPrivacyRequestFieldSnapshot(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            field_name=row.field_name,
            field_label=row.field_label,
            encrypted_value_present=bool(row.encrypted_value),
            hashed_value_present=bool(row.hashed_value),
            is_hash_migrated=getattr(row, "is_hash_migrated", None),
        )
        for row in rows
    ]


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


def get_request_task_sub_requests(
    privacy_request_id: str, db: Session
) -> List[RequestTaskSubRequestSnapshot]:
    """Fetch request task sub-requests and project into non-PII snapshots."""

    rows = (
        db.query(
            RequestTaskSubRequest.id,
            RequestTaskSubRequest.created_at,
            RequestTaskSubRequest.updated_at,
            RequestTaskSubRequest.request_task_id,
            RequestTaskSubRequest.status,
            RequestTaskSubRequest.rows_masked,
        )
        .join(RequestTask, RequestTask.id == RequestTaskSubRequest.request_task_id)
        .filter(RequestTask.privacy_request_id == privacy_request_id)
        .order_by(RequestTaskSubRequest.created_at.asc())
        .all()
    )

    return [
        RequestTaskSubRequestSnapshot(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            request_task_id=row.request_task_id,
            status=row.status,
            rows_masked=row.rows_masked,
        )
        for row in rows
    ]


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


def get_storage_configs(
    privacy_request_id: str, db: Session
) -> List[StorageConfigSnapshot]:
    """Fetch storage configs referenced by the privacy request's attachments."""

    storage_keys = (
        db.query(Attachment.storage_key)
        .join(AttachmentReference)
        .filter(
            AttachmentReference.reference_id == privacy_request_id,
            AttachmentReference.reference_type == AttachmentReferenceType.privacy_request,
        )
        .distinct()
        .all()
    )
    keys = [row[0] for row in storage_keys if row and row[0]]
    if not keys:
        return []

    rows = (
        db.query(
            StorageConfig.key,
            StorageConfig.name,
            StorageConfig.type,
            StorageConfig.format,
            StorageConfig.is_default,
        )
        .filter(StorageConfig.key.in_(keys))
        .order_by(StorageConfig.key.asc())
        .all()
    )

    return [
        StorageConfigSnapshot(
            key=row.key,
            name=row.name,
            type=getattr(row.type, "value", str(row.type)),
            format=getattr(row.format, "value", str(row.format))
            if row.format is not None
            else None,
            is_default=bool(row.is_default),
        )
        for row in rows
    ]


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


def get_dataset_configs(
    privacy_request_id: str, db: Session
) -> List[DatasetConfigSnapshot]:
    """Fetch dataset configs relevant to this privacy request (based on request tasks)."""

    dataset_keys_rows = (
        db.query(RequestTask.dataset_name)
        .filter(RequestTask.privacy_request_id == privacy_request_id)
        .distinct()
        .all()
    )
    dataset_keys = [r[0] for r in dataset_keys_rows if r and r[0]]
    if not dataset_keys:
        return []

    rows = (
        db.query(DatasetConfig)
        .filter(DatasetConfig.fides_key.in_(dataset_keys))
        .order_by(DatasetConfig.fides_key.asc())
        .all()
    )

    return [
        DatasetConfigSnapshot(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            fides_key=row.fides_key,
            connection_config_id=row.connection_config_id,
            ctl_dataset_id=row.ctl_dataset_id,
        )
        for row in rows
    ]


class CtlDatasetSnapshot(BaseModel):
    """
    Diagnostics projection of a single CTL `ctl_datasets` row.

    Non-PII only: excludes full dataset JSON (collections/meta).
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    fides_key: str
    name: Optional[str] = None


def get_ctl_datasets(
    privacy_request_id: str, db: Session
) -> List[CtlDatasetSnapshot]:
    """Fetch CTL datasets referenced by relevant DatasetConfigs."""

    dataset_configs = get_dataset_configs(privacy_request_id, db)
    ctl_ids = [dc.ctl_dataset_id for dc in dataset_configs]
    if not ctl_ids:
        return []

    rows = (
        db.query(CtlDataset)
        .filter(CtlDataset.id.in_(ctl_ids))
        .order_by(CtlDataset.fides_key.asc())
        .all()
    )

    return [
        CtlDatasetSnapshot(
            id=row.id,
            fides_key=row.fides_key,
            name=row.name,
        )
        for row in rows
    ]


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


def get_messaging_config(db: Session) -> Optional[MessagingConfigSnapshot]:
    """Fetch the active default messaging config (if any) as a non-PII snapshot."""

    cfg = MessagingConfig.get_active_default(db)
    if not cfg:
        return None

    return MessagingConfigSnapshot(
        key=cfg.key,
        name=cfg.name,
        service_type=getattr(cfg.service_type, "value", str(cfg.service_type)),
        last_test_timestamp=cfg.last_test_timestamp,
        last_test_succeeded=cfg.last_test_succeeded,
    )


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


def get_manual_tasks(
    privacy_request_id: str, db: Session
) -> List[ManualTaskSnapshot]:
    """Fetch manual tasks related to this privacy request (via ManualTaskInstance)."""

    task_ids_rows = (
        db.query(ManualTaskInstance.task_id)
        .filter(
            ManualTaskInstance.entity_id == privacy_request_id,
            ManualTaskInstance.entity_type == ManualTaskEntityType.privacy_request,
        )
        .distinct()
        .all()
    )
    task_ids = [r[0] for r in task_ids_rows if r and r[0]]
    if not task_ids:
        return []

    tasks = (
        db.query(ManualTask)
        .filter(ManualTask.id.in_(task_ids))
        .order_by(ManualTask.created_at.asc())
        .all()
    )

    return [
        ManualTaskSnapshot(
            id=t.id,
            created_at=t.created_at,
            updated_at=t.updated_at,
            task_type=getattr(t.task_type, "value", str(t.task_type)),
            parent_entity_id=t.parent_entity_id,
            parent_entity_type=getattr(
                t.parent_entity_type, "value", str(t.parent_entity_type)
            ),
        )
        for t in tasks
    ]


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


def get_manual_task_instances(
    privacy_request_id: str, db: Session
) -> List[ManualTaskInstanceSnapshot]:
    """Fetch manual task instances for this privacy request."""

    instances = (
        db.query(ManualTaskInstance)
        .filter(
            ManualTaskInstance.entity_id == privacy_request_id,
            ManualTaskInstance.entity_type == ManualTaskEntityType.privacy_request,
        )
        .order_by(ManualTaskInstance.created_at.asc())
        .all()
    )

    return [
        ManualTaskInstanceSnapshot(
            id=i.id,
            created_at=i.created_at,
            updated_at=i.updated_at,
            task_id=i.task_id,
            config_id=i.config_id,
            entity_id=i.entity_id,
            entity_type=getattr(i.entity_type, "value", str(i.entity_type)),
            status=getattr(i.status, "value", str(i.status)),
            completed_at=i.completed_at,
            due_date=i.due_date,
        )
        for i in instances
    ]


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


def get_manual_task_configs(
    privacy_request_id: str, db: Session
) -> List[ManualTaskConfigSnapshot]:
    """Fetch manual task configs relevant to this privacy request (via instances)."""

    config_ids_rows = (
        db.query(ManualTaskInstance.config_id)
        .filter(
            ManualTaskInstance.entity_id == privacy_request_id,
            ManualTaskInstance.entity_type == ManualTaskEntityType.privacy_request,
        )
        .distinct()
        .all()
    )
    config_ids = [r[0] for r in config_ids_rows if r and r[0]]
    if not config_ids:
        return []

    configs = (
        db.query(ManualTaskConfig)
        .filter(ManualTaskConfig.id.in_(config_ids))
        .order_by(ManualTaskConfig.created_at.asc())
        .all()
    )

    return [
        ManualTaskConfigSnapshot(
            id=c.id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            task_id=c.task_id,
            config_type=getattr(c.config_type, "value", str(c.config_type)),
            version=int(c.version),
            is_current=bool(c.is_current),
            execution_timing=getattr(
                c.execution_timing, "value", str(c.execution_timing)
            ),
        )
        for c in configs
    ]


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


def get_manual_task_config_fields(
    privacy_request_id: str, db: Session
) -> List[ManualTaskConfigFieldSnapshot]:
    """Fetch manual task config fields relevant to this privacy request (via configs)."""

    configs = get_manual_task_configs(privacy_request_id, db)
    config_ids = [c.id for c in configs]
    if not config_ids:
        return []

    fields = (
        db.query(ManualTaskConfigField)
        .filter(ManualTaskConfigField.config_id.in_(config_ids))
        .order_by(ManualTaskConfigField.created_at.asc())
        .all()
    )

    return [
        ManualTaskConfigFieldSnapshot(
            id=f.id,
            created_at=f.created_at,
            updated_at=f.updated_at,
            task_id=f.task_id,
            config_id=f.config_id,
            field_key=f.field_key,
            field_type=getattr(f.field_type, "value", str(f.field_type)),
            execution_timing=getattr(f.execution_timing, "value", str(f.execution_timing))
            if f.execution_timing is not None
            else None,
        )
        for f in fields
    ]


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


def get_manual_task_references(
    privacy_request_id: str, db: Session
) -> List[ManualTaskReferenceSnapshot]:
    """Fetch manual task references for tasks relevant to this privacy request."""

    tasks = get_manual_tasks(privacy_request_id, db)
    task_ids = [t.id for t in tasks]
    if not task_ids:
        return []

    refs = (
        db.query(ManualTaskReference)
        .filter(ManualTaskReference.task_id.in_(task_ids))
        .order_by(ManualTaskReference.created_at.asc())
        .all()
    )

    snapshots: List[ManualTaskReferenceSnapshot] = []
    for ref in refs:
        reference_type = getattr(ref.reference_type, "value", str(ref.reference_type))
        reference_id: Optional[str] = ref.reference_id
        if reference_type == ManualTaskReferenceType.assigned_user.value:
            reference_id = None
        snapshots.append(
            ManualTaskReferenceSnapshot(
                id=ref.id,
                created_at=ref.created_at,
                updated_at=ref.updated_at,
                task_id=ref.task_id,
                reference_type=reference_type,
                reference_id=reference_id,
                config_field_key=ref.config_field_key,
            )
        )
    return snapshots


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


def get_manual_task_submissions(
    privacy_request_id: str, db: Session
) -> List[ManualTaskSubmissionSnapshot]:
    """Fetch manual task submissions for this privacy request (via instances)."""

    instance_ids_rows = (
        db.query(ManualTaskInstance.id)
        .filter(
            ManualTaskInstance.entity_id == privacy_request_id,
            ManualTaskInstance.entity_type == ManualTaskEntityType.privacy_request,
        )
        .all()
    )
    instance_ids = [r[0] for r in instance_ids_rows if r and r[0]]
    if not instance_ids:
        return []

    subs = (
        db.query(ManualTaskSubmission)
        .filter(ManualTaskSubmission.instance_id.in_(instance_ids))
        .order_by(ManualTaskSubmission.submitted_at.asc())
        .all()
    )

    return [
        ManualTaskSubmissionSnapshot(
            id=s.id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            task_id=s.task_id,
            config_id=s.config_id,
            field_id=s.field_id,
            instance_id=s.instance_id,
            submitted_at=s.submitted_at,
        )
        for s in subs
    ]


class ManualTaskConditionalDependencySnapshot(BaseModel):
    """
    Diagnostics projection of a single `manual_task_conditional_dependency` row.

    Non-PII only: excludes condition tree contents.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    manual_task_id: str
    config_field_key: Optional[str] = None


def get_manual_task_conditional_dependencies(
    privacy_request_id: str, db: Session
) -> List[ManualTaskConditionalDependencySnapshot]:
    """Fetch manual task conditional dependency rows for tasks relevant to this privacy request."""

    tasks = get_manual_tasks(privacy_request_id, db)
    task_ids = [t.id for t in tasks]
    if not task_ids:
        return []

    deps = (
        db.query(ManualTaskConditionalDependency)
        .filter(ManualTaskConditionalDependency.manual_task_id.in_(task_ids))
        .order_by(ManualTaskConditionalDependency.id.asc())
        .all()
    )

    return [
        ManualTaskConditionalDependencySnapshot(
            id=d.id,
            manual_task_id=d.manual_task_id,
            config_field_key=d.config_field_key,
        )
        for d in deps
    ]


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


def get_privacy_request_diagnostics(
    privacy_request_id: str, db: Session
) -> PrivacyRequestDiagnostics:
    """Create a `PrivacyRequestDiagnostics` object for the given privacy request id."""

    return PrivacyRequestDiagnostics(
        privacy_request=get_privacy_request_snapshot(privacy_request_id, db),
        privacy_request_error=get_privacy_request_error(privacy_request_id, db),
        custom_privacy_request_fields=get_custom_privacy_request_fields(
            privacy_request_id, db
        ),
        provided_identities=get_provided_identities(privacy_request_id, db),
        execution_logs=get_execution_logs(privacy_request_id, db),
        audit_logs=get_audit_logs(privacy_request_id, db),
        request_tasks=get_request_tasks(privacy_request_id, db),
        request_task_sub_requests=get_request_task_sub_requests(
            privacy_request_id, db
        ),
        dataset_configs=get_dataset_configs(privacy_request_id, db),
        ctl_datasets=get_ctl_datasets(privacy_request_id, db),
        storage_configs=get_storage_configs(privacy_request_id, db),
        messaging_config=get_messaging_config(db),
        manual_tasks=get_manual_tasks(privacy_request_id, db),
        manual_task_instances=get_manual_task_instances(privacy_request_id, db),
        manual_task_references=get_manual_task_references(privacy_request_id, db),
        manual_task_configs=get_manual_task_configs(privacy_request_id, db),
        manual_task_config_fields=get_manual_task_config_fields(privacy_request_id, db),
        manual_task_submissions=get_manual_task_submissions(privacy_request_id, db),
        manual_task_conditional_dependencies=get_manual_task_conditional_dependencies(
            privacy_request_id, db
        ),
        attachments=get_attachments(privacy_request_id, db),
        attachment_references=get_attachment_references(privacy_request_id, db),
        comments=get_comments(privacy_request_id, db),
        comment_references=get_comment_references(privacy_request_id, db),
    )