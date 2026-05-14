"""Data-access layer for ``AttachmentUserProvided`` rows."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.future import select
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
        field_name: str,
        property_id: str,
        policy_key: str,
        session: Session,
    ) -> AttachmentUserProvidedRecord:
        """Insert a new ``uploaded`` row; flush so ``id`` is populated."""
        row = AttachmentUserProvided(
            object_key=object_key,
            status=AttachmentUserProvidedStatus.uploaded,
            storage_key=storage_key,
            field_name=field_name,
            property_id=property_id,
            policy_key=policy_key,
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return AttachmentUserProvidedRecord.from_orm(row)

    @staticmethod
    def lock_by_ids(
        ids: list[str], *, session: Session
    ) -> dict[str, AttachmentUserProvided]:
        """Lock matching rows under ``FOR UPDATE``, keyed by id.

        ``session`` is required — the lock is only meaningful inside a
        caller-owned transaction. Ordered by ``id`` to give all callers the
        same lock-acquisition order (deadlock-safe across overlapping
        batches). Returns rows in *any* state; missing ids are absent from
        the dict. Pair with :meth:`assert_all_uploaded` to enforce the
        lifecycle precondition.
        """
        if not ids:
            return {}
        query = (
            select(AttachmentUserProvided)
            .where(AttachmentUserProvided.id.in_(ids))
            .order_by(AttachmentUserProvided.id)
            .with_for_update()
        )
        rows = session.execute(query).scalars().all()
        return {row.id: row for row in rows}

    @staticmethod
    def assert_all_uploaded(rows: list[AttachmentUserProvided]) -> None:
        """Raise :class:`InvalidAttachmentStateError` on first non-``uploaded`` row."""
        for row in rows:
            if row.status != AttachmentUserProvidedStatus.uploaded:
                raise InvalidAttachmentStateError(row.object_key, row.status)

    @staticmethod
    def mark_promoted(
        row: AttachmentUserProvided,
        *,
        promoted_at: Optional[datetime] = None,
    ) -> None:
        """Flip ``uploaded`` → ``promoted`` (in-session). Caller owns commit."""
        if row.status != AttachmentUserProvidedStatus.uploaded:
            raise InvalidAttachmentStateError(row.object_key, row.status)
        row.status = AttachmentUserProvidedStatus.promoted
        row.promoted_at = promoted_at or datetime.now(timezone.utc)

    @staticmethod
    def mark_deleted(row: AttachmentUserProvided) -> None:
        """Transition a row to ``deleted`` (in-session, no commit)."""
        row.status = AttachmentUserProvidedStatus.deleted

    @with_optional_sync_session
    def list_uploaded_older_than(
        self,
        cutoff: datetime,
        *,
        limit: int = 1000,
        session: Session,
    ) -> list[AttachmentUserProvided]:
        """Return ``uploaded`` rows created before ``cutoff`` (exclusive), oldest first, capped at ``limit``."""
        query = (
            select(AttachmentUserProvided)
            .where(
                AttachmentUserProvided.status == AttachmentUserProvidedStatus.uploaded,
                AttachmentUserProvided.created_at < cutoff,
            )
            .order_by(AttachmentUserProvided.created_at.asc())
            .limit(limit)
        )
        return list(session.execute(query).scalars().all())
