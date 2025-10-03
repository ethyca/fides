import enum
from typing import Any, List

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import text

from fides.api.db.util import EnumColumn


class ExecutionLogStatus(enum.Enum):
    """Enum for task execution log statuses, reflecting where they are in their workflow"""

    in_processing = "in_processing"
    pending = "pending"
    complete = "complete"
    error = "error"
    awaiting_processing = "paused"  # "paused" in the database to avoid a migration, but use "awaiting_processing" in the app
    retrying = "retrying"
    skipped = "skipped"
    polling = "polling"


# Statuses that can be resumed
RESUMABLE_EXECUTION_LOG_STATUSES = [
    ExecutionLogStatus.pending,
    ExecutionLogStatus.polling,
]


class WorkerTask:
    """
    A task for a worker to execute.
    """

    # Field called action_type to avoid migrations in RequestTask when creating this model
    action_type = Column(String, nullable=False, index=True)
    # Note that WorkerTask share statuses with ExecutionLogs.  When a WorkerTask changes state, an ExecutionLog
    # is also created with that state.  These are tied tightly together in GraphTask.
    status = Column(
        EnumColumn(
            ExecutionLogStatus,
            native_enum=False,
            values_callable=lambda x: [
                i.value for i in x
            ],  # Using ExecutionLogStatus values in database, even though app is using the names.
        ),  # character varying in database
        index=True,
        nullable=False,
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        action_type = kwargs.get("action_type")
        if action_type is not None:
            self.validate_action_type(action_type)
        super().__init__(*args, **kwargs)

    @classmethod
    def validate_action_type(cls, action_type: str) -> None:
        """
        Validates that the action type is allowed for the worker task.
        """
        if action_type not in cls.allowed_action_types():
            raise ValueError(f"Invalid action_type '{action_type}' for {cls.__name__}")

    @classmethod
    def allowed_action_types(cls) -> List[str]:
        """
        Subclasses must implement this method to return a list of allowed action types.
        """
        raise NotImplementedError("Subclasses must implement allowed_action_types")


class TaskExecutionLog:
    """
    Stores the individual execution logs associated with a WorkerTask.
    """

    status = Column(
        EnumColumn(
            ExecutionLogStatus,
            native_enum=True,
            values_callable=lambda x: [
                i.value for i in x
            ],  # Using ExecutionLogStatus values in database, even though app is using the names.
        ),
        index=True,
        nullable=False,
    )
    # Contains info, warning, or error messages
    message = Column(String)

    # Use clock_timestamp() instead of NOW() to get the actual current time at row creation,
    # regardless of transaction state. This prevents timestamp caching within transactions
    # and ensures more accurate creation times.
    # https://www.postgresql.org/docs/current/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT

    created_at = Column(
        DateTime(timezone=True), server_default=text("clock_timestamp()")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("clock_timestamp()"),
        onupdate=text("clock_timestamp()"),
    )
