"""Data-access layer for ``AttachmentUserProvided`` rows.

Encapsulates every SQLAlchemy query and mutation the attachment
user-provided service needs, so the service layer can stay focused on
storage I/O, validation, and the pending → promoted → deleted state
machine.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)


class AttachmentUserProvidedRepository:
    """DB reads/writes for ``attachment_user_provided``."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create_pending(
        self, *, object_key: str, storage_key: str
    ) -> AttachmentUserProvided:
        """Insert a new ``pending`` row (in-session, no commit).

        Flushes so the caller can read server-generated columns (``id``,
        ``created_at``). The caller owns the transaction — the row is
        visible to the same session and rolls back if the caller does.
        """
        row = AttachmentUserProvided(
            object_key=object_key,
            status=AttachmentUserProvidedStatus.pending,
            storage_key=storage_key,
        )
        self._db.add(row)
        self._db.flush()
        self._db.refresh(row)
        return row

    def mark_promoted(
        self,
        rows: list[AttachmentUserProvided],
        *,
        promoted_at: Optional[datetime] = None,
    ) -> None:
        """Flip rows from ``pending`` to ``promoted`` (in-session, no commit).

        Caller owns the transaction — mutations are visible to the same
        session and roll back if the caller does.

        Raises:
            ValueError: A row is not in ``pending``.
        """
        now = promoted_at or datetime.now(timezone.utc)
        for row in rows:
            if row.status != AttachmentUserProvidedStatus.pending:
                raise ValueError(
                    f"Attachment '{row.object_key}' is in state {row.status}, "
                    "expected 'pending'. Refusing to promote."
                )
            row.status = AttachmentUserProvidedStatus.promoted
            row.promoted_at = now

    def mark_deleted(self, row: AttachmentUserProvided) -> None:
        """Transition a row to ``deleted`` (in-session, no commit)."""
        row.status = AttachmentUserProvidedStatus.deleted

    def lock_pending_by_ids(self, ids: list[str]) -> list[AttachmentUserProvided]:
        """Return ``pending`` rows matching ``ids`` under ``FOR UPDATE``.

        The lock is released by any ``COMMIT`` (or ``ROLLBACK``) on the
        caller's session — including commits issued by downstream
        ``Base.create`` calls. The authoritative concurrency guard is
        :meth:`mark_promoted`'s ``row.status != pending`` check.
        """
        return (
            self._db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id.in_(ids))
            .filter(
                AttachmentUserProvided.status == AttachmentUserProvidedStatus.pending
            )
            .with_for_update()
            .all()
        )

    def list_pending_older_than(self, cutoff: datetime) -> list[AttachmentUserProvided]:
        """Return every ``pending`` row created before ``cutoff``."""
        return (
            self._db.query(AttachmentUserProvided)
            .filter(
                AttachmentUserProvided.status == AttachmentUserProvidedStatus.pending
            )
            .filter(AttachmentUserProvided.created_at < cutoff)
            .all()
        )
