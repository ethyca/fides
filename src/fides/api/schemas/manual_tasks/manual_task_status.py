from datetime import datetime, timezone
from enum import Enum as EnumType
from typing import Optional

from sqlalchemy.orm import Session


class StatusTransitionNotAllowed(Exception):
    """Exception raised when a status transition is not allowed."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class StatusType(str, EnumType):
    """Enum for manual task status."""

    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"

    @classmethod
    def get_valid_transitions(cls, current_status: "StatusType") -> list["StatusType"]:
        """Get valid transitions from the current status.

        Args:
            current_status: The current status

        Returns:
            list[StatusType]: List of valid transitions
        """
        if current_status == cls.pending:
            return [cls.in_progress, cls.failed]
        if current_status == cls.in_progress:
            return [cls.completed, cls.failed]
        if current_status == cls.completed:
            return []
        if current_status == cls.failed:
            return [cls.pending, cls.in_progress]
        return []


class StatusTransitionMixin:
    """Mixin for handling status transitions.

    This mixin provides methods for managing status transitions and completion tracking.
    It can be used by any model that needs status management.
    """

    # These should be overridden by the implementing class
    status: StatusType
    completed_at: Optional[datetime]
    completed_by_id: Optional[str]

    def _get_valid_transitions(self) -> list[StatusType]:
        """Get valid transitions from the current status.

        Returns:
            list[StatusType]: List of valid transitions
        """
        return StatusType.get_valid_transitions(self.status)

    def _validate_status_transition(self, new_status: StatusType) -> None:
        """Validate that a status transition is allowed.

        Args:
            new_status: The new status to transition to

        Raises:
            StatusTransitionNotAllowed: If the transition is not allowed
        """
        # Don't allow transitions to the same status
        if new_status == self.status:
            raise StatusTransitionNotAllowed(
                f"Invalid status transition: already in status {new_status}"
            )

        # Get valid transitions for current status
        valid_transitions = self._get_valid_transitions()
        if new_status not in valid_transitions:
            raise StatusTransitionNotAllowed(
                f"Invalid status transition from {self.status} to {new_status}. "
                f"Valid transitions are: {valid_transitions}"
            )

    def update_status(
        self, db: Session, new_status: StatusType, user_id: Optional[str] = None
    ) -> None:
        """Update the status with validation and completion handling.

        Args:
            db: Database session
            new_status: New status to set
            user_id: Optional user ID who is making the change
        """
        self._validate_status_transition(new_status)

        if new_status == StatusType.completed:
            self.completed_at = datetime.now(timezone.utc)
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
