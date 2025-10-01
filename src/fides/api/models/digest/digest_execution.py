"""
Models for tracking digest task execution state and progress.

This module provides database models to track digest task execution state,
enabling graceful resumption after worker interruptions.
"""

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn
from fides.api.models.worker_task import WorkerTask


class DigestExecutionStatus(enum.Enum):
    """Status enum for digest task execution tracking."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class DigestTaskExecution(WorkerTask, Base):
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

    # Execution state
    status = Column(
        EnumColumn(DigestExecutionStatus),
        nullable=False,
        default=DigestExecutionStatus.PENDING,
        index=True,
    )

    # Progress tracking
    total_recipients = Column(Integer, nullable=True)
    processed_recipients = Column(Integer, nullable=False, default=0)
    successful_emails = Column(Integer, nullable=False, default=0)
    failed_emails = Column(Integer, nullable=False, default=0)

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
        self.status = DigestExecutionStatus.IN_PROGRESS
        self.celery_task_id = celery_task_id
        self.started_at = func.now()
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
        self.successful_emails = successful_count
        self.failed_emails = failed_count
        self.processed_user_ids = processed_user_ids
        self.last_checkpoint_at = func.now()

        if execution_state:
            self.execution_state = execution_state

        self.save(db)

    def mark_completed(self, db: Session) -> None:
        """Mark the execution as completed."""
        self.status = DigestExecutionStatus.COMPLETED
        self.completed_at = func.now()
        self.save(db)

    def mark_failed(self, db: Session, error_message: str) -> None:
        """Mark the execution as failed."""
        self.status = DigestExecutionStatus.FAILED
        self.error_message = error_message
        self.completed_at = func.now()
        self.save(db)

    def mark_interrupted(self, db: Session) -> None:
        """Mark the execution as interrupted (for later resumption)."""
        self.status = DigestExecutionStatus.INTERRUPTED
        self.save(db)

    def can_resume(self) -> bool:
        """Check if this execution can be resumed."""
        return (
            self.status
            in [DigestExecutionStatus.INTERRUPTED, DigestExecutionStatus.IN_PROGRESS]
            and self.processed_user_ids is not None
        )

    def get_remaining_work(self) -> Dict[str, Any]:
        """Get information about remaining work for resumption."""
        return {
            "processed_user_ids": self.processed_user_ids or [],
            "execution_state": self.execution_state or {},
            "processed_count": self.processed_recipients or 0,
            "successful_count": self.successful_emails,
            "failed_count": self.failed_emails,
        }
