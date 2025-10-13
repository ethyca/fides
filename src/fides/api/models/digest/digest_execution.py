from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql import func

from fides.api.db.base_class import Base
from fides.api.models.worker_task import ExecutionLogStatus, WorkerTask

if TYPE_CHECKING:
    from fides.api.models.digest.digest_config import DigestConfig


class DigestTaskExecution(
    WorkerTask, Base
):  # pylint: disable=too-many-instance-attributes
    """
    Model for tracking digest task execution state and progress.

    This model enables graceful resumption of digest tasks after worker
    interruptions by persisting execution state and progress information.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "digest_task_execution"

    # Foreign key to digest config
    digest_config_id = Column(
        String,
        ForeignKey("digest_config.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Celery task tracking
    celery_task_id = Column(String, nullable=True, index=True)

    # Progress tracking
    total_recipients = Column(Integer, nullable=True)
    processed_recipients = Column(Integer, nullable=False, default=0)
    successful_communications = Column(Integer, nullable=False, default=0)
    failed_communications = Column(Integer, nullable=False, default=0)

    # State persistence for resumption
    execution_state = Column(JSONB, nullable=True, default={})
    processed_user_ids = Column(JSONB, nullable=True, default=[])

    # Timing information
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_checkpoint_at = Column(DateTime(timezone=True), nullable=True)

    # Error information
    error_message = Column(Text, nullable=True)

    # Relationships
    digest_config = relationship("DigestConfig", back_populates="executions")

    @classmethod
    def allowed_action_types(cls) -> List[str]:
        """Return allowed action types for digest task execution."""
        return ["digest_processing"]

    def mark_started(self, db: Session, celery_task_id: str) -> None:
        """Mark the execution as started."""
        self.status = ExecutionLogStatus.in_processing
        self.celery_task_id = celery_task_id
        self.started_at = func.now()
        self.save(db)

    def mark_awaiting_processing(self, db: Session) -> None:
        """Mark the execution as awaiting processing."""
        self.status = ExecutionLogStatus.awaiting_processing
        self.save(db)

    def update_progress(
        self,
        db: Session,
        processed_count: int,
        successful_count: int,
        failed_count: int,
        processed_user_ids: List[str],
        execution_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update execution progress and create checkpoint."""
        self.processed_recipients = processed_count
        self.successful_communications = successful_count
        self.failed_communications = failed_count
        self.processed_user_ids = processed_user_ids
        self.last_checkpoint_at = func.now()

        # Mark JSONB fields as modified so SQLAlchemy knows they changed
        flag_modified(self, "processed_user_ids")

        if execution_state:
            self.execution_state = execution_state
            flag_modified(self, "execution_state")

        self.save(db)

    def mark_completed(self, db: Session) -> None:
        """Mark the execution as completed."""
        self.status = ExecutionLogStatus.complete
        self.completed_at = func.now()
        self.save(db)

    def mark_failed(self, db: Session, error_message: str) -> None:
        """Mark the execution as failed."""
        self.status = ExecutionLogStatus.error
        self.error_message = error_message
        self.completed_at = func.now()
        self.save(db)

    def can_resume(self) -> bool:
        """Check if this execution can be resumed."""
        return (
            self.status
            in [
                ExecutionLogStatus.in_processing,
                ExecutionLogStatus.awaiting_processing,
            ]
            and self.processed_user_ids is not None
        )

    def get_remaining_work(self) -> Dict[str, Any]:
        """Get information about remaining work for resumption."""
        # Ensure processed_user_ids is always a list
        raw_processed_user_ids = self.processed_user_ids or []
        processed_user_ids = (
            raw_processed_user_ids if isinstance(raw_processed_user_ids, list) else []
        )
        return {
            "processed_user_ids": processed_user_ids,
            "execution_state": self.execution_state or {},
            "processed_count": self.processed_recipients or 0,
            "successful_count": self.successful_communications,
            "failed_count": self.failed_communications,
        }
