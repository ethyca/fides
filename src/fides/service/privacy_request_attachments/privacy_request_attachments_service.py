"""Upload, resolve, and promote service for data-subject-uploaded file attachments."""

import os
import posixpath
from io import BytesIO
from typing import Any, Optional
from uuid import uuid4

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    AttachmentReferenceType,
    AttachmentType,
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.models.storage import StorageConfig, get_active_default_storage_config
from fides.api.schemas.attachment import PrivacyRequestAttachment
from fides.api.schemas.privacy_center_config import DEFAULT_FILE_MAX_SIZE_BYTES
from fides.api.schemas.redis_cache import CustomPrivacyRequestField
from fides.api.schemas.storage.storage import StorageType
from fides.api.service.storage.providers import StorageProviderFactory
from fides.api.service.storage.providers.base import StorageProvider
from fides.api.service.storage.util import AllowedFileType, FilesMagicBytes
from fides.common.session_management import with_optional_sync_session
from fides.config import CONFIG
from fides.service.attachment_service import AttachmentService
from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
    AttachmentNotFoundError,
    DisallowedFileTypeError,
    FileTooLargeError,
    InvalidAttachmentValueError,
    StorageBucketNotConfiguredError,
    StorageNotConfiguredError,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_repository import (
    AttachmentUserProvidedRepository,
)

DEFAULT_MAX_SIZE_BYTES = DEFAULT_FILE_MAX_SIZE_BYTES
UPLOAD_READ_CHUNK_BYTES = 64 * 1024

OBJECT_KEY_PREFIX = "privacy_request_attachments"


def _bucket(storage_config: StorageConfig) -> str:
    return (storage_config.details or {}).get("bucket", "")


def _get_provider_and_bucket(
    db: Session,
) -> tuple[StorageProvider, str, StorageConfig]:
    """Return (provider, bucket, storage_config) or raise a domain error."""
    storage_config = get_active_default_storage_config(db)
    if not storage_config:
        raise StorageNotConfiguredError()
    bucket = _bucket(storage_config)
    if not bucket and storage_config.type != StorageType.local:
        raise StorageBucketNotConfiguredError()
    provider = StorageProviderFactory.create(storage_config)
    return provider, bucket, storage_config


class AttachmentUserProvidedService:
    """Validate, store, and register data-subject-uploaded attachments."""

    def __init__(self, repo: Optional[AttachmentUserProvidedRepository] = None) -> None:
        self._repo = repo or AttachmentUserProvidedRepository()

    @with_optional_sync_session
    def upload_attachment(
        self,
        *,
        file_data: bytes,
        session: Session,
    ) -> PrivacyRequestAttachment:
        """Validate, store, and register a file attachment. Object key is
        server-generated; client filename + Content-Type are discarded.

        Raises ``FileTooLargeError``, ``DisallowedFileTypeError``,
        ``StorageNotConfiguredError``, or ``StorageBucketNotConfiguredError``.
        """
        if len(file_data) > DEFAULT_MAX_SIZE_BYTES:
            raise FileTooLargeError(DEFAULT_MAX_SIZE_BYTES)

        allowed = FilesMagicBytes.default_public_upload_allowed_file_types()
        sig = FilesMagicBytes.from_bytes(file_data)
        if sig is None or sig not in allowed:
            raise DisallowedFileTypeError(sorted(allowed))

        content_type = AllowedFileType[sig].value
        provider, bucket, storage_config = _get_provider_and_bucket(session)
        object_key = posixpath.join(OBJECT_KEY_PREFIX, f"{uuid4()}.{sig}")

        # Insert + flush DB row before the storage write. If the upload
        # raises, the row rolls back and no orphan file is created. If
        # the upload succeeds, the row commits alongside it; the orphan
        # sweep keys on rows in ``uploaded`` state to catch any leftover
        # files (see ``AttachmentUserProvidedStatus``).
        record = self._repo.create_uploaded(
            object_key=object_key,
            storage_key=storage_config.key,
            session=session,
        )
        result = provider.upload(
            bucket=bucket,
            key=object_key,
            data=BytesIO(file_data),
            content_type=content_type,
        )

        logger.info(
            "Uploaded attachment id={} size={} type={}",
            record.id,
            result.file_size,
            content_type,
        )

        return PrivacyRequestAttachment(id=record.id)

    @with_optional_sync_session
    def resolve_file_attachments(
        self,
        custom_privacy_request_fields: Optional[dict[str, CustomPrivacyRequestField]],
        file_field_names: set[str],
        *,
        session: Session,
    ) -> list[AttachmentUserProvided]:
        """Resolve file-field values to ``uploaded`` rows under ``FOR UPDATE``.

        Returns the locked ORM rows so :meth:`promote_rows_to_attachments`
        can mutate them in the same transaction. The lock holds until the
        caller's next commit/rollback. Returns ``[]`` if the
        ``allow_custom_privacy_request_field_collection`` flag is off.
        """
        if not custom_privacy_request_fields or not file_field_names:
            return []

        if not CONFIG.execution.allow_custom_privacy_request_field_collection:
            return []

        rows: list[AttachmentUserProvided] = []
        for name in file_field_names:
            field = custom_privacy_request_fields.get(name)
            if field is None:
                continue

            value = field.value
            if not isinstance(value, list) or not all(
                isinstance(v, str) for v in value
            ):
                raise InvalidAttachmentValueError(name)
            ids: list[str] = [v for v in value if isinstance(v, str)]
            if not ids:
                continue

            pending = {
                r.id: r for r in self._repo.lock_uploaded_by_ids(ids, session=session)
            }
            for item in ids:
                row = pending.get(item)
                if row is None:
                    raise AttachmentNotFoundError(name)
                rows.append(row)

        return rows

    @with_optional_sync_session
    def promote_rows_to_attachments(
        self,
        privacy_request: PrivacyRequest,
        rows: list[AttachmentUserProvided],
        *,
        session: Session,
    ) -> None:
        """Transition pending rows → ``promoted`` and create ``Attachment`` records."""
        if not rows:
            return

        self._repo.assert_all_uploaded(rows)

        provider, bucket, storage_config = _get_provider_and_bucket(session)
        attachment_service = AttachmentService(db=session)

        # ``(row, attachment)`` pairs we have already promoted in-memory.
        # On a mid-loop failure we use this to undo BOTH the Attachment
        # records and the in-memory ``promoted`` flips so a caller commit
        # (e.g. ``privacy_request.delete``) cannot persist a ``promoted``
        # row that points at no Attachment.
        created: list[tuple[AttachmentUserProvided, Any]] = []
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
                # Flip only after a successful create_and_upload so the
                # row's status invariant tracks Attachment existence.
                self._repo.mark_promoted(row, session=session)
                created.append((row, attachment))
                logger.info(
                    "Promoted attachment {} on request {} → Attachment {}",
                    row.id,
                    privacy_request.id,
                    attachment.id,
                )
        except Exception:
            for row, attachment in created:
                try:
                    attachment_service.delete(attachment)
                except Exception:
                    logger.warning(
                        "Failed to clean up partially-created Attachment {} after "
                        "promotion failure",
                        attachment.id,
                        exc_info=True,
                    )
                row.status = AttachmentUserProvidedStatus.uploaded
                row.promoted_at = None
            raise

        # Phase 3: best-effort delete of temp objects.
        for row in rows:
            try:
                provider.delete(bucket, row.object_key)
            except Exception:
                logger.warning(
                    "Could not delete temporary file {} after promotion",
                    row.object_key,
                    exc_info=True,
                )
