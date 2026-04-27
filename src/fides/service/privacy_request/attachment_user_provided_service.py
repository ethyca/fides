"""Service layer for data-subject-uploaded file attachments.

Lifecycle (DB-backed state machine on ``attachment_user_provided``):

    (no row) ──upload──▶ uploaded ──claim──▶ promoted

Responsibilities:
- Upload raw bytes to the active default storage backend and insert an
  ``uploaded`` row.
- Identify which custom-field values reference uploaded rows and return
  the rows ready for promotion (``resolve_file_attachments``).
- Atomically transition uploaded → promoted and create ``Attachment`` rows
  linked to each promoted user-provided row (``promote_rows_to_attachments``).

The orphan-sweep cleanup that takes ``uploaded`` rows to ``deleted`` ships
in a follow-up branch.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, Optional
from uuid import uuid4

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    AttachmentReferenceType,
    AttachmentType,
    AttachmentUserProvided,
)
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.models.storage import StorageConfig, get_active_default_storage_config
from fides.api.schemas.attachment import PrivacyRequestAttachment
from fides.api.schemas.privacy_center_config import DEFAULT_FILE_MAX_SIZE_BYTES
from fides.api.schemas.redis_cache import CustomPrivacyRequestField
from fides.api.service.storage.providers import StorageProviderFactory
from fides.api.service.storage.providers.base import StorageProvider
from fides.api.service.storage.util import (
    FilesMagicBytes,
    PublicUploadAllowedFileTypes,
    extension_for_mime,
)
from fides.config import CONFIG
from fides.service.attachment_service import AttachmentService
from fides.service.privacy_request.attachment_user_provided_repository import (
    AttachmentUserProvidedRepository,
)

# Re-export under a shorter local alias for the endpoint + internal use.
DEFAULT_MAX_SIZE_BYTES = DEFAULT_FILE_MAX_SIZE_BYTES

# Chunk size for streaming uploads — abort as soon as cumulative size exceeds
# DEFAULT_MAX_SIZE_BYTES so an attacker cannot buffer an unbounded body.
UPLOAD_READ_CHUNK_BYTES = 64 * 1024

OBJECT_KEY_PREFIX = "privacy_request_attachments/"


def _bucket(storage_config: StorageConfig) -> str:
    return (storage_config.details or {}).get("bucket", "")


def _get_provider_and_bucket(
    db: Session,
) -> tuple[StorageProvider, str, StorageConfig]:
    """Return (provider, bucket, storage_config) or raise RuntimeError.

    Centralises the three-way lookup used by upload, promotion, and orphan
    cleanup so callers share the same error path.
    """
    storage_config = get_active_default_storage_config(db)
    if not storage_config:
        raise RuntimeError(
            "No active default storage configuration found. "
            "Configure a storage backend before accepting file attachments."
        )
    provider = StorageProviderFactory.create(storage_config)
    return provider, _bucket(storage_config), storage_config


def upload_attachment(
    *,
    file_data: bytes,
    db: Session,
) -> PrivacyRequestAttachment:
    """Validate, store, and register a file attachment.

    Writes the file under ``privacy_request_attachments/{uuid}.{ext}``
    using the active default storage backend and inserts an
    ``AttachmentUserProvided`` row with status ``pending``. The original
    client-supplied filename is discarded — the stored name is entirely
    server-generated, eliminating a class of path/metadata-injection
    risks at the storage boundary.

    File type is determined purely from magic-byte inspection; the
    client-declared Content-Type is ignored. Size is enforced via
    ``DEFAULT_MAX_SIZE_BYTES``.

    Raises:
        ValueError: File fails size or type validation.
        RuntimeError: No active storage config found.
    """
    if len(file_data) > DEFAULT_MAX_SIZE_BYTES:
        raise ValueError(
            f"File exceeds maximum allowed size of {DEFAULT_MAX_SIZE_BYTES} bytes "
            f"(received {len(file_data)} bytes)"
        )

    allowed = PublicUploadAllowedFileTypes.mime_types()
    content_type = FilesMagicBytes.from_bytes(file_data)
    if content_type is None or content_type not in allowed:
        raise ValueError(f"File type is not allowed. Allowed types: {sorted(allowed)}")

    provider, bucket, storage_config = _get_provider_and_bucket(db)
    object_key = f"{OBJECT_KEY_PREFIX}{uuid4()}.{extension_for_mime(content_type)}"
    result = provider.upload(
        bucket=bucket,
        key=object_key,
        data=BytesIO(file_data),
        content_type=content_type,
    )

    row = AttachmentUserProvidedRepository(db).create_uploaded(
        object_key=object_key,
        storage_key=storage_config.key,
    )
    db.commit()

    logger.info(
        "Uploaded attachment id={} size={} type={}",
        row.id,
        result.file_size,
        content_type,
    )

    return PrivacyRequestAttachment(id=row.id)


def resolve_file_attachments(
    custom_privacy_request_fields: Optional[Dict[str, CustomPrivacyRequestField]],
    file_field_names: set[str],
    db: Session,
) -> list[AttachmentUserProvided]:
    """Resolve file-field values to ``AttachmentUserProvided`` rows.

    ``file_field_names`` is authoritative — derived from the Privacy Center
    config's ``field_type == "file"`` entries. For each listed field, each
    id in its ``value`` list is looked up against the pending rows. The
    caller is responsible for stripping the file-field keys from the
    payload before persisting the remaining custom fields.

    Lock semantics: ``lock_uploaded_by_ids`` issues ``FOR UPDATE``, but any
    subsequent ``db.commit()`` on the caller's session releases that lock.
    The authoritative concurrency guard is the ``row.status != pending``
    check inside :func:`AttachmentUserProvidedRepository.mark_promoted`;
    a racing promotion on the same row causes that check to raise and the
    caller to roll back. The lock is a best-effort optimisation to reduce
    the race window, not a hard guarantee.

    Status transitions do NOT happen here; they are deferred to
    :func:`promote_rows_to_attachments` so that if privacy-request
    creation rolls back, pending rows stay pending.

    Raises:
        ValueError: A file field's value is malformed (not a list of
            strings) or any id fails to resolve to a pending row.
    """
    if not custom_privacy_request_fields or not file_field_names:
        return []

    if not CONFIG.execution.allow_custom_privacy_request_field_collection:
        return []

    rows: list[AttachmentUserProvided] = []
    repo = AttachmentUserProvidedRepository(db)

    for name in file_field_names:
        field = custom_privacy_request_fields.get(name)
        if field is None:
            continue

        value = field.value
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ValueError(
                f"File attachment for field '{name}' must be a list of attachment ids."
            )
        ids: list[str] = [v for v in value if isinstance(v, str)]
        if not ids:
            continue

        pending = {r.id: r for r in repo.lock_uploaded_by_ids(ids)}
        for item in ids:
            row = pending.get(item)
            if row is None:
                raise ValueError(
                    f"File attachment for field '{name}' "
                    "has expired or is invalid. Please re-upload and resubmit."
                )
            rows.append(row)

    return rows


def promote_rows_to_attachments(
    privacy_request: PrivacyRequest,
    db: Session,
    rows: list[AttachmentUserProvided],
) -> None:
    """Transition pending rows → promoted and create ``Attachment`` records.

    Three phases:
    1. Flip every row's status to ``promoted`` (they were locked ``FOR
       UPDATE`` by :func:`resolve_file_attachments`).
    2. Download each row's bytes and create an ``Attachment`` record
       linked to the privacy request. ``AttachmentService.create_and_upload``
       commits per row — this function tracks those so a mid-loop failure
       can explicitly delete the partial work.
    3. Delete the temp objects from storage (best-effort — orphan sweep
       reaps leftovers under ``privacy_request_attachments/``).

    Raises:
        Exception: Re-raises any storage or AttachmentService error after
            deleting any ``Attachment`` rows already created on this call.
            Caller should still delete the privacy request itself.
    """
    if not rows:
        return

    provider, bucket, storage_config = _get_provider_and_bucket(db)
    attachment_service = AttachmentService(db=db)
    repo = AttachmentUserProvidedRepository(db)

    # Phase 1: flip status under the already-held FOR UPDATE lock.
    repo.mark_promoted(rows)

    # Phase 2: download + create Attachment rows.  Each iteration commits
    # (Attachment._create_record + AttachmentReference.create). Track what
    # we've created so partial failure can be compensated explicitly —
    # AttachmentReference has no FK cascade on reference_id, so deleting
    # the privacy_request alone would orphan any rows created before the
    # failure. filename is the last path segment of the object_key, which
    # is server-generated (uuid + extension) — no user-supplied name is
    # preserved.
    created: list[Any] = []
    try:
        for row in rows:
            file_content = provider.download(bucket, row.object_key)
            file_name = os.path.basename(row.object_key)
            attachment = attachment_service.create_and_upload(
                data={
                    "file_name": file_name,
                    "user_id": None,
                    "username": "data_subject",
                    "attachment_type": AttachmentType.user_provided,
                    "storage_key": storage_config.key,
                },
                file_data=file_content,
                references=[
                    {
                        "reference_id": privacy_request.id,
                        "reference_type": AttachmentReferenceType.privacy_request,
                    }
                ],
            )
            created.append(attachment)
            logger.info(
                "Promoted attachment {} on request {} → Attachment {}",
                row.id,
                privacy_request.id,
                attachment.id,
            )
    except Exception:
        for attachment in created:
            try:
                attachment_service.delete(attachment)
            except Exception:
                logger.warning(
                    "Failed to clean up partially-created Attachment {} after "
                    "promotion failure",
                    attachment.id,
                    exc_info=True,
                )
        raise

    # Phase 3: delete temp objects.  Failures here are logged only — the row
    # is now ``promoted`` so the orphan sweep (which targets ``pending``
    # only) won't pick it up. Leftover storage objects under this prefix
    # become dead weight; see the ticket for follow-up on a promoted-row
    # storage-reconciliation sweep.
    for row in rows:
        try:
            provider.delete(bucket, row.object_key)
        except Exception:
            logger.warning(
                "Could not delete temporary file {} after promotion",
                row.object_key,
                exc_info=True,
            )
