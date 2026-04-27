"""Data-access layer for ``AttachmentUserProvided`` rows.

Encapsulates every SQLAlchemy query and mutation the attachment
user-provided service needs for upload + promotion. Cleanup-side
methods (``mark_deleted`` / ``list_uploaded_older_than``) ship in the
follow-up branch that adds the orphan-sweep task.
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

    def create_uploaded(
        self, *, object_key: str, storage_key: str
    ) -> AttachmentUserProvided:
        """Insert a new ``uploaded`` row (in-session, no commit).

        Flushes so the caller can read server-generated columns (``id``,
        ``created_at``). The caller owns the transaction — the row is
        visible to the same session and rolls back if the caller does.
        """
        row = AttachmentUserProvided(
            object_key=object_key,
            status=AttachmentUserProvidedStatus.uploaded,
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
        """Flip rows from ``uploaded`` to ``promoted`` (in-session, no commit).

        Caller owns the transaction — mutations are visible to the same
        session and roll back if the caller does.

        Raises:
            ValueError: A row is not in ``uploaded``.
        """
        now = promoted_at or datetime.now(timezone.utc)
        for row in rows:
            if row.status != AttachmentUserProvidedStatus.uploaded:
                raise ValueError(
                    f"Attachment '{row.object_key}' is in state {row.status}, "
                    "expected 'uploaded'. Refusing to promote."
                )
            row.status = AttachmentUserProvidedStatus.promoted
            row.promoted_at = now

    def lock_uploaded_by_ids(self, ids: list[str]) -> list[AttachmentUserProvided]:
        """Return ``uploaded`` rows matching ``ids`` under ``FOR UPDATE``.

        The lock is released by any ``COMMIT`` (or ``ROLLBACK``) on the
        caller's session — including commits issued by downstream
        ``Base.create`` calls. The authoritative concurrency guard is
        :meth:`mark_promoted`'s ``row.status != uploaded`` check.
        """
        return (
            self._db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id.in_(ids))
            .filter(
                AttachmentUserProvided.status == AttachmentUserProvidedStatus.uploaded
            )
            .with_for_update()
            .all()
        )
