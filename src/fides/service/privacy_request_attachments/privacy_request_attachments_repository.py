"""Data-access layer for ``AttachmentUserProvided`` rows."""

from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)
from fides.common.session_management import with_optional_sync_session
from fides.service.privacy_request_attachments.privacy_request_attachments_entities import (
    AttachmentUserProvidedRecord,
)


class AttachmentUserProvidedRepository:
    """DB reads/writes for ``attachment_user_provided``."""

    @with_optional_sync_session
    def create_uploaded(
        self,
        *,
        object_key: str,
        storage_key: str,
        session: Session,
    ) -> AttachmentUserProvidedRecord:
        """Insert a new ``uploaded`` row; flush so ``id`` is populated."""
        row = AttachmentUserProvided(
            object_key=object_key,
            status=AttachmentUserProvidedStatus.uploaded,
            storage_key=storage_key,
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return AttachmentUserProvidedRecord.from_orm(row)
