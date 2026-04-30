"""Upload service for data-subject-uploaded file attachments."""

import posixpath
from io import BytesIO
from typing import Optional
from uuid import uuid4

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.storage import StorageConfig, get_active_default_storage_config
from fides.api.schemas.attachment import PrivacyRequestAttachment
from fides.api.schemas.privacy_center_config import DEFAULT_FILE_MAX_SIZE_BYTES
from fides.api.service.storage.providers import StorageProviderFactory
from fides.api.service.storage.providers.base import StorageProvider
from fides.api.service.storage.util import AllowedFileType, FilesMagicBytes
from fides.common.session_management import with_optional_sync_session
from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
    DisallowedFileTypeError,
    FileTooLargeError,
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
    if not bucket:
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
