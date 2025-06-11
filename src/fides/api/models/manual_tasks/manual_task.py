from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskLogStatus,
    ManualTaskParentEntityType,
    ManualTaskReferenceType,
    ManualTaskType,
)


class ManualTask(Base):
    """Model for storing manual tasks.

    This model can be used for both privacy request tasks and general tasks.
    For privacy requests, it replaces the functionality of manual webhooks.
    For other use cases, it provides a flexible task management system.

    There can only be one ManualTask per parent entity.
    You can create multiple Configs for the same ManualTask.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "manual_task"

    # Database columns
    task_type = Column(
        EnumColumn(ManualTaskType),
        nullable=False,
        default=ManualTaskType.privacy_request,
    )
    parent_entity_id = Column(String, nullable=False)
    parent_entity_type = Column(
        EnumColumn(ManualTaskParentEntityType),
        nullable=False,
        default=ManualTaskParentEntityType.connection_config,
    )
    due_date = Column(DateTime, nullable=True)

    # Relationships
    references = relationship(
        "ManualTaskReference",
        back_populates="task",
        uselist=True,
        cascade="all, delete-orphan",
    )
    logs = relationship(
        "ManualTaskLog",
        back_populates="task",
        primaryjoin="and_(ManualTask.id == ManualTaskLog.task_id)",
        viewonly=True,
        order_by="ManualTaskLog.created_at",
    )

    # Properties
    @property
    def assigned_users(self) -> list[str]:
        """Get all users assigned to this task."""
        if not self.references:
            return []
        return [
            ref.reference_id
            for ref in self.references
            if ref.reference_type == ManualTaskReferenceType.assigned_user
        ]

    # CRUD Operations
    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = True
    ) -> "ManualTask":
        """Create a new manual task."""
        task = super().create(db=db, data=data, check_name=check_name)
        ManualTaskLog.create_log(
            db=db,
            task_id=task.id,
            status=ManualTaskLogStatus.created,
            message=f"Created manual task for {data['task_type']}",
        )
        return task


class ManualTaskReference(Base):
    """Join table to associate manual tasks with multiple references.

    A single task may have many references including privacy requests, configurations, and assigned users.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "manual_task_reference"

    # Database columns
    task_id = Column(
        String, ForeignKey("manual_task.id", ondelete="CASCADE"), nullable=False
    )
    reference_id = Column(String, nullable=False)
    reference_type = Column(EnumColumn(ManualTaskReferenceType), nullable=False)

    # Relationships
    task = relationship("ManualTask", back_populates="references")
