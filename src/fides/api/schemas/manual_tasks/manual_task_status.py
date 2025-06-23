from datetime import datetime, timezone
from enum import Enum as EnumType
from typing import Optional, Protocol

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
        """Get valid transitions from the current status."""
        transitions = {
            cls.pending: [cls.in_progress, cls.failed, cls.completed],
            cls.in_progress: [cls.completed, cls.failed],
            cls.completed: [],
            cls.failed: [cls.pending, cls.in_progress],
        }
        return transitions.get(current_status, [])


class StatusTransitionProtocol(Protocol):
    """Protocol for objects that support status transitions.

    This protocol defines the interface that any object supporting status transitions
    must implement. It includes both the required attributes and methods.

    Example:
        ```python
        # Any class that implements this protocol can be used interchangeably
        def process_status_update(obj: StatusTransitionProtocol, db: Session) -> None:
            if obj.is_pending:
                obj.start_progress(db)
            elif obj.is_in_progress:
                obj.mark_completed(db, user_id="user123")

        # This works with ManualTaskInstance or any other class implementing the protocol
        instance = ManualTaskInstance(...)
        process_status_update(instance, db)
        ```
    """

    # Required attributes - using runtime types that work with SQLAlchemy
    status: StatusType
    completed_at: Optional[datetime]  # Can be None when resetting to pending
    completed_by_id: Optional[str]  # Can be None when resetting to pending

    # Required methods
    # pylint does not understand the Protocol abstract syntax and will complain about the ellipsis
    def update_status(
        self, db: Session, new_status: StatusType, user_id: Optional[str] = None
    ) -> None:
        """Update the status with validation and completion handling."""
        ...  # pylint: disable=unnecessary-ellipsis

    def mark_completed(self, db: Session, user_id: str) -> None:
        """Mark as completed."""
        ...  # pylint: disable=unnecessary-ellipsis

    def mark_failed(self, db: Session) -> None:
        """Mark as failed."""
        ...  # pylint: disable=unnecessary-ellipsis

    def start_progress(self, db: Session) -> None:
        """Mark as in progress."""
        ...  # pylint: disable=unnecessary-ellipsis

    def reset_to_pending(self, db: Session) -> None:
        """Reset to pending status."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def is_completed(self) -> bool:
        """Check if completed."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def is_failed(self) -> bool:
        """Check if failed."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def is_in_progress(self) -> bool:
        """Check if in progress."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def is_pending(self) -> bool:
        """Check if pending."""
        ...  # pylint: disable=unnecessary-ellipsis


def validate_status_transition_object(obj: StatusTransitionProtocol) -> bool:
    """Validate that an object properly implements the StatusTransitionProtocol.

    This function demonstrates how the Protocol can be used for runtime validation
    and type checking.
    """
    required_attrs = ["status", "completed_at", "completed_by_id"]
    required_methods = [
        "update_status",
        "mark_completed",
        "mark_failed",
        "start_progress",
        "reset_to_pending",
    ]
    required_properties = ["is_completed", "is_failed", "is_in_progress", "is_pending"]

    # Check all required elements
    all_required = required_attrs + required_methods + required_properties
    return all(hasattr(obj, attr) for attr in all_required) and all(
        callable(getattr(obj, method)) for method in required_methods
    )


class StatusTransitionMixin:
    """Mixin for handling status transitions.

    This mixin provides methods for managing status transitions and completion tracking.
    It implements the StatusTransitionProtocol and can be used by any model that needs status management.
    """

    # Type annotations to match the Protocol
    status: StatusType
    completed_at: Optional[datetime]
    completed_by_id: Optional[str]

    def _get_valid_transitions(self) -> list[StatusType]:
        """Get valid transitions from the current status."""
        return StatusType.get_valid_transitions(self.status)

    def _validate_status_transition(self, new_status: StatusType) -> None:
        """Validate that a status transition is allowed."""
        if new_status == self.status:
            raise StatusTransitionNotAllowed(
                f"Invalid status transition: already in status {new_status}"
            )

        valid_transitions = self._get_valid_transitions()
        if new_status not in valid_transitions:
            raise StatusTransitionNotAllowed(
                f"Invalid status transition from {self.status} to {new_status}. "
                f"Valid transitions are: {valid_transitions}"
            )

    def update_status(
        self, db: Session, new_status: StatusType, user_id: Optional[str] = None
    ) -> None:
        """Update the status with validation and completion handling."""
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
        """Mark as completed."""
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
