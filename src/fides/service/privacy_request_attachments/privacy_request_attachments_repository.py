"""Data-access layer for ``AttachmentUserProvided`` rows."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)
from fides.common.session_management import with_optional_sync_session
from fides.service.privacy_request_attachments.privacy_request_attachments_entities import (
    AttachmentUserProvidedRecord,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
    InvalidAttachmentStateError,
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

    @with_optional_sync_session
    def lock_uploaded_by_ids(
        self, ids: list[str], *, session: Session
    ) -> list[AttachmentUserProvided]:
        """Return ``uploaded`` rows matching ``ids`` under ``FOR UPDATE``.

        Returns ORM rows so the caller can mutate via :meth:`mark_promoted`
        within the same transaction. The lock is released by the caller's
        next ``COMMIT``/``ROLLBACK``; the authoritative concurrency guard
        is :meth:`mark_promoted`'s ``status != uploaded`` check.
        """
        return (
            session.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id.in_(ids))
            .filter(
                AttachmentUserProvided.status == AttachmentUserProvidedStatus.uploaded
            )
            .with_for_update()
            .all()
        )

    @staticmethod
    def assert_all_uploaded(rows: list[AttachmentUserProvided]) -> None:
        """Raise :class:`InvalidAttachmentStateError` if any row is not in
        ``uploaded``. Caller uses this to fail fast before mutating state."""
        for row in rows:
            if row.status != AttachmentUserProvidedStatus.uploaded:
                raise InvalidAttachmentStateError(row.object_key, row.status)

    @with_optional_sync_session
    def mark_promoted(
        self,
        row: AttachmentUserProvided,
        *,
        promoted_at: Optional[datetime] = None,
        session: Session,  # pylint: disable=unused-argument
    ) -> None:
        """Flip a single row from ``uploaded`` to ``promoted``.

        Raises :class:`InvalidAttachmentStateError` if the row is not in
        ``uploaded``. Per-row so callers can flip after each successful
        side effect; a mid-batch failure leaves remaining rows alone.
        """
        if row.status != AttachmentUserProvidedStatus.uploaded:
            raise InvalidAttachmentStateError(row.object_key, row.status)
        row.status = AttachmentUserProvidedStatus.promoted
        row.promoted_at = promoted_at or datetime.now(timezone.utc)
