"""Upload, resolve, and promote service for data-subject-uploaded file attachments."""

import os
import posixpath
from io import BytesIO
from typing import Any, Optional
from uuid import uuid4

from loguru import logger
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    AttachmentReferenceType,
    AttachmentType,
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)
from fides.api.models.privacy_center_config import (
    PrivacyCenterConfig as PrivacyCenterConfigModel,
)
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.models.property import Property
from fides.api.models.storage import StorageConfig, get_active_default_storage_config
from fides.api.schemas.attachment import PrivacyRequestAttachment
from fides.api.schemas.privacy_center_config import FileUploadCustomPrivacyRequestField
from fides.api.schemas.privacy_center_config import (
    PrivacyCenterConfig as PrivacyCenterConfigSchema,
)
from fides.api.schemas.redis_cache import CustomPrivacyRequestField
from fides.api.schemas.storage.storage import StorageType
from fides.api.service.storage.providers import StorageProviderFactory
from fides.api.service.storage.providers.base import StorageProvider
from fides.api.service.storage.util import (
    DEFAULT_FILE_MAX_SIZE_BYTES,
    AllowedFileType,
    FilesMagicBytes,
    FileUploadConstraints,
)
from fides.common.session_management import with_optional_sync_session
from fides.config import CONFIG
from fides.service.attachment_service import AttachmentService
from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
    AttachmentContextMismatchError,
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


def _resolve_privacy_center_config_dict(
    db: Session, property_id: Optional[str]
) -> Optional[dict[str, Any]]:
    """Return privacy-center config: property_id → default property → global table."""
    if property_id:
        prop = Property.get_by(db, field="id", value=property_id)
        cfg = prop.privacy_center_config if prop else None
        if cfg:
            return cfg
    default_prop = Property.get_by(db, field="is_default", value=True)
    cfg = default_prop.privacy_center_config if default_prop else None
    if cfg:
        return cfg
    record = PrivacyCenterConfigModel.filter(
        db=db,
        conditions=PrivacyCenterConfigModel.single_row,  # type: ignore[arg-type]
    ).first()
    if record:
        return record.config  # type: ignore[return-value]
    return None


def resolve_upload_constraints(
    db: Session,
    *,
    property_id: Optional[str],
    policy_key: Optional[str],
    field_name: Optional[str],
) -> FileUploadConstraints:
    """Resolve upload constraints for a file field.

    All three keyword arguments are required — callers pass ``None`` to
    opt into the default-property / no-policy / no-field fallbacks
    rather than silently relying on omitted parameters.

    Returns the constraints of the ``FileUploadCustomPrivacyRequestField``
    matching ``field_name`` inside the action whose ``policy_key`` matches
    ``policy_key``. Mirrors the action-scoping that
    :class:`PrivacyRequestService` applies at submission so the upload
    path and the submission path resolve identical constraints.

    Falls back to :meth:`FileUploadConstraints.defaults` when any of
    ``policy_key`` / ``field_name`` is ``None``, the config can't be
    resolved/parsed, no action matches the policy_key, or no matching
    file field exists in that action.
    """
    if not field_name or not policy_key:
        return FileUploadConstraints.defaults()

    config_dict = _resolve_privacy_center_config_dict(db, property_id)
    if not config_dict:
        return FileUploadConstraints.defaults()

    try:
        cfg = PrivacyCenterConfigSchema.model_validate(config_dict)
    except ValidationError as exc:
        logger.warning("Could not parse Privacy Center config for upload: {}", exc)
        return FileUploadConstraints.defaults()

    for action in cfg.actions:
        if action.policy_key != policy_key:
            continue
        fields = action.custom_privacy_request_fields or {}
        candidate = fields.get(field_name)
        if isinstance(candidate, FileUploadCustomPrivacyRequestField):
            return FileUploadConstraints(
                max_size_bytes=candidate.max_size_bytes,
                allowed_file_types=frozenset(candidate.allowed_file_types),
            )
        break
    return FileUploadConstraints.defaults()


class AttachmentUserProvidedService:
    """Validate, store, and register data-subject-uploaded attachments."""

    def __init__(self, repo: Optional[AttachmentUserProvidedRepository] = None) -> None:
        self._repo = repo or AttachmentUserProvidedRepository()

    @staticmethod
    def _resolve_extension(
        file_data: bytes,
        constraints: "FileUploadConstraints",
        client_filename: Optional[str],
    ) -> str:
        """Pick the file extension to record for this upload.

        1. If magic-byte candidates intersect the allow-list, use that
           intersection. The client-claimed extension wins when present
           in the intersection; otherwise pick the first sorted entry
           for determinism. Resolves ZIP-family collisions
           (``docx``/``xlsx``/``zip`` all match ``PK\\x03\\x04``).
        2. If no magic-byte signature matches at all (e.g. CSV, TXT),
           fall back to the client-claimed extension iff it is in the
           allow-list.
        3. Otherwise raise :class:`DisallowedFileTypeError`.
        """
        candidates = FilesMagicBytes.candidates(file_data)
        allowed_intersection = candidates & constraints.allowed_file_types
        client_ext = (
            client_filename.rsplit(".", 1)[-1].lower()
            if client_filename and "." in client_filename
            else None
        )

        if allowed_intersection:
            if client_ext and client_ext in allowed_intersection:
                return client_ext
            return sorted(allowed_intersection)[0]

        if (
            not candidates
            and client_ext
            and client_ext in constraints.allowed_file_types
        ):
            return client_ext

        raise DisallowedFileTypeError(sorted(constraints.allowed_file_types))

    @with_optional_sync_session
    def upload_attachment(
        self,
        *,
        file_data: bytes,
        session: Session,
        constraints: "FileUploadConstraints",
        field_name: str,
        property_id: str,
        policy_key: str,
        client_filename: Optional[str] = None,
    ) -> PrivacyRequestAttachment:
        """Validate, store, and register a file attachment. Object key is
        server-generated; client Content-Type is discarded.

        ``constraints`` carries the resolved size + allowed extensions
        for this upload; the dataclass self-validates so a single
        magic-byte check is sufficient here.

        ``field_name`` + ``property_id`` are persisted on the row so the
        submission flow can verify the upload was made in the same
        ``(property, field)`` context it's being claimed under.

        ``client_filename`` is consulted only to disambiguate ZIP-family
        magic-byte collisions and as a last-resort fallback when the file
        has no recognizable magic prefix (CSV, TXT). The chosen extension
        must still be in ``constraints.allowed_file_types``.

        Raises ``FileTooLargeError``, ``DisallowedFileTypeError``,
        ``StorageNotConfiguredError``, or ``StorageBucketNotConfiguredError``.
        """
        if len(file_data) > constraints.max_size_bytes:
            raise FileTooLargeError(constraints.max_size_bytes)

        extension = self._resolve_extension(
            file_data, constraints, client_filename
        )

        content_type = AllowedFileType[extension].value
        provider, bucket, storage_config = _get_provider_and_bucket(session)
        object_key = posixpath.join(OBJECT_KEY_PREFIX, f"{uuid4()}.{extension}")

        # Insert + flush DB row before the storage write. If the upload
        # raises, the row rolls back and no orphan file is created. If
        # the upload succeeds, the row commits alongside it; the orphan
        # sweep keys on rows in ``uploaded`` state to catch any leftover
        # files (see ``AttachmentUserProvidedStatus``).
        record = self._repo.create_uploaded(
            object_key=object_key,
            storage_key=storage_config.key,
            field_name=field_name,
            property_id=property_id,
            policy_key=policy_key,
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
        property_id: str,
        policy_key: str,
        *,
        session: Session,
    ) -> list[AttachmentUserProvided]:
        """Resolve file-field values to ``uploaded`` rows under ``FOR UPDATE``.

        Per-row validation: ``row.field_name`` must equal the field name
        being resolved, ``row.property_id`` must equal the submission's
        ``property_id``, and ``row.policy_key`` must equal the
        submission's ``policy_key``. Mismatches raise
        :class:`AttachmentContextMismatchError`.

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
                if (
                    row.field_name != name
                    or row.property_id != property_id
                    or row.policy_key != policy_key
                ):
                    raise AttachmentContextMismatchError(
                        attachment_id=row.id,
                        expected_field=name,
                        actual_field=row.field_name,
                        expected_property=property_id,
                        actual_property=row.property_id,
                        expected_policy=policy_key,
                        actual_policy=row.policy_key,
                    )
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
        """Transition pending rows → ``promoted`` and create ``Attachment`` records.

        Re-validates ``row.property_id == privacy_request.property_id``
        per row before any state change — defense in depth on top of the
        resolve-time check.
        """
        if not rows:
            return

        for row in rows:
            if (
                row.property_id != privacy_request.property_id
                or row.policy_key != privacy_request.policy.key
            ):
                raise AttachmentContextMismatchError(
                    attachment_id=row.id,
                    expected_field=row.field_name,
                    actual_field=row.field_name,
                    expected_property=privacy_request.property_id or "",
                    actual_property=row.property_id,
                    expected_policy=privacy_request.policy.key,
                    actual_policy=row.policy_key,
                )

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
