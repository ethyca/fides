from typing import TYPE_CHECKING, Any

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func

from fides.api.db.base_class import Base, FidesBase
from fides.api.db.util import EnumColumn
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskLogStatus,
    ManualTaskParentEntityType,
    ManualTaskReferenceType,
    ManualTaskType,
)

if TYPE_CHECKING:  # pragma: no cover
    from fides.api.models.manual_tasks.manual_task_config import (  # pragma: no cover
        ManualTaskConfig,
    )
    from fides.api.models.manual_tasks.manual_task_instance import (
        ManualTaskInstance,
        ManualTaskSubmission,
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

    # redefined here because there's a minor, unintended discrepancy between
    # this `id` field and that of the `Base` class, which explicitly sets `index=True`.
    # TODO: we likely should _not_ be setting `index=True` on the `id`
    # attribute of the `Base` class, as `primary_key=True` already specifies a
    # primary key constraint, which will implicitly create an index for the field.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

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

    __table_args__ = (
        UniqueConstraint(
            "parent_entity_id",
            "parent_entity_type",
            name="uq_manual_task_parent_entity",
        ),
        Index("ix_manual_task_parent_entity", "parent_entity_type", "parent_entity_id"),
        Index("ix_manual_task_task_type", "task_type"),
    )

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
    configs = relationship(
        "ManualTaskConfig",
        back_populates="task",
        cascade="all, delete-orphan",
        uselist=True,
    )
    instances = relationship(
        "ManualTaskInstance",
        back_populates="task",
        viewonly=True,
        uselist=True,
    )
    submissions = relationship(
        "ManualTaskSubmission",
        back_populates="task",
        uselist=True,
        viewonly=True,
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

    # redefined here because there's a minor, unintended discrepancy between
    # this `id` field and that of the `Base` class, which explicitly sets `index=True`.
    # TODO: we likely should _not_ be setting `index=True` on the `id`
    # attribute of the `Base` class, as `primary_key=True` already specifies a
    # primary key constraint, which will implicitly create an index for the field.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Database columns
    task_id = Column(
        String, ForeignKey("manual_task.id", ondelete="CASCADE"), nullable=False
    )
    reference_id = Column(String, nullable=False)
    reference_type = Column(EnumColumn(ManualTaskReferenceType), nullable=False)

    __table_args__ = (
        Index("ix_manual_task_reference_reference", "reference_id", "reference_type"),
        Index("ix_manual_task_reference_task_id", "task_id"),
    )

    # Relationships
    task = relationship("ManualTask", back_populates="references", viewonly=True)
