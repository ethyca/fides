from enum import Enum as EnumType
from typing import Optional, Any
from sqlalchemy import Column, String, ForeignKey, JSONB, DateTime
from sqlalchemy.orm import relationship, Session
from datetime import datetime, UTC

from fides.api.db.base_class import Base


class ManualTaskLogStatus(str, EnumType):
    """Enum for manual task log status."""
    in_processing = "in_processing"
    complete = "complete"
    error = "error"
    retrying = "retrying"
    paused = "paused"
    awaiting_input = "awaiting_input"


class ManualTaskLog(Base):
    """Model for storing manual task execution logs."""
    __tablename__ = "manual_task_log"

    task_id = Column(String, ForeignKey("manual_task.id"), nullable=False)
    config_id = Column(String, ForeignKey("manual_task_config.id"), nullable=True)
    instance_id = Column(String, ForeignKey("manual_task_instance.id"), nullable=True)
    status = Column(String, nullable=False)
    message = Column(String, nullable=True)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now(UTC))

    # Relationships
    task = relationship("ManualTask", back_populates="logs")

    @classmethod
    def create_log(
        cls,
        db: Session,
        status: ManualTaskLogStatus,
        task_id: str,
        config_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Create a new task log entry.

        Args:
            db: Database session
            task_id: ID of the task
            status: Status of the log entry
            message: Optional message describing the event
            details: Optional additional details about the event
        """
        data = {
            "task_id": task_id,
            "config_id": config_id,
            "instance_id": instance_id,
            "status": status,
            "message": message,
            "details": details,
        }
        cls.create(db=db, data=data)
