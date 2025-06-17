from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus

if TYPE_CHECKING:  # pragma: no cover
    from fides.api.models.manual_tasks.manual_task import ManualTask  # pragma: no cover
    from fides.api.models.manual_tasks.manual_task_config import (
        ManualTaskConfig,  # pragma: no cover
    )


class ManualTaskLog(Base):
    """Model for storing manual task execution logs."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "manual_task_log"

    task_id = Column(
        String, ForeignKey("manual_task.id", ondelete="CASCADE"), nullable=False
    )
    config_id = Column(String, ForeignKey("manual_task_config.id"), nullable=True)
    instance_id = Column(String, nullable=True)
    status = Column(String, nullable=False)
    message = Column(String, nullable=False)
    details = Column(JSONB, nullable=True)

    # Relationships - using string references to avoid circular imports
    task = relationship("ManualTask", back_populates="logs", foreign_keys=[task_id])
    config = relationship(
        "ManualTaskConfig", back_populates="logs", foreign_keys=[config_id]
    )
    # TODO: Add instance relationship when it is implemented
    # instance = relationship("ManualTaskInstance", back_populates="logs")

    @classmethod
    def create_log(
        cls,
        db: Session,
        task_id: str,
        status: ManualTaskLogStatus,
        message: str,
        config_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> "ManualTaskLog":
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
        return cls.create(db=db, data=data)

    @classmethod
    def create_error_log(
        cls,
        db: Session,
        task_id: str,
        message: str,
        config_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> "ManualTaskLog":
        """Create a new error log entry.

        Args:
            db: Database session
            task_id: ID of the task
            message: Error message describing what went wrong
            config_id: Optional ID of the configuration
            instance_id: Optional ID of the instance
            details: Optional additional details about the error

        Returns:
            The created error log entry
        """
        return cls.create_log(
            db=db,
            status=ManualTaskLogStatus.error,
            task_id=task_id,
            config_id=config_id,
            instance_id=instance_id,
            message=message,
            details=details,
        )
