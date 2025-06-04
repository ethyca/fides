from enum import Enum as EnumType
from typing import Optional, TypeVar, Generic
from datetime import datetime, UTC
from sqlalchemy.orm import Session


class StatusType(str, EnumType):
    """Enum for manual task status."""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


T = TypeVar('T', bound=StatusType)


class StatusTransitionMixin(Generic[T]):
    """Mixin for handling status transitions.

    This mixin provides methods for managing status transitions and completion tracking.
    It can be used by any model that needs status management.
    """

    # These should be overridden by the implementing class
    status: T
    completed_at: Optional[datetime]
    completed_by_id: Optional[str]

    def _validate_status_transition(self, new_status: T) -> None:
        """Validate that the status transition is allowed."""
        valid_transitions = {
            StatusType.pending: [StatusType.in_progress, StatusType.failed],
            StatusType.in_progress: [StatusType.completed, StatusType.failed],
            StatusType.completed: [],  # No transitions from completed
            StatusType.failed: [StatusType.pending],  # Can retry from failed
        }

        if new_status not in valid_transitions.get(self.status, []):
            raise ValueError(
                f"Invalid status transition from {self.status} to {new_status}. "
                f"Valid transitions are: {valid_transitions.get(self.status, [])}"
            )

    def update_status(
        self, db: Session, new_status: T, user_id: Optional[str] = None
    ) -> None:
        """Update the status with validation and completion handling.

        Args:
            db: Database session
            new_status: New status to set
            user_id: Optional user ID who is making the change
        """
        self._validate_status_transition(new_status)

        if new_status == StatusType.completed:
            self.completed_at = datetime.now(UTC)
            self.completed_by_id = user_id
        elif new_status == StatusType.pending:
            # Reset completion fields if going back to pending
            self.completed_at = None
            self.completed_by_id = None

        self.status = new_status
        db.add(self)
        db.commit()

    def mark_completed(self, db: Session, user_id: str) -> None:
        """Mark as completed.

        Args:
            db: Database session
            user_id: user ID who completed the task
        """
        self.update_status(db, StatusType.completed, user_id)

    def mark_failed(self, db: Session) -> None:
        """Mark as failed."""
        self.update_status(db, StatusType.failed)

    def start_progress(self, db: Session) -> None:
        """Mark as in progress."""
        self.update_status(db, StatusType.in_progress)

    def reset_to_pending(self, db: Session) -> None:
        """Reset to pending status."""
        self.update_status(db, StatusType.pending)

    @property
    def is_completed(self) -> bool:
        """Check if completed."""
        return self.status == StatusType.completed

    @property
    def is_failed(self) -> bool:
        """Check if failed."""
        return self.status == StatusType.failed

    @property
    def is_in_progress(self) -> bool:
        """Check if in progress."""
        return self.status == StatusType.in_progress

    @property
    def is_pending(self) -> bool:
        """Check if pending."""
        return self.status == StatusType.pending
