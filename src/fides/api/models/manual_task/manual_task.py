from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, Optional, cast

from pydantic import ConfigDict, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func

from fides.api.db.base_class import Base, FidesBase
from fides.api.db.util import EnumColumn
from fides.api.request_context import get_user_id
from fides.api.schemas.base_class import FidesSchema

if TYPE_CHECKING:
    from fides.api.models.attachment import Attachment
    from fides.api.models.fides_user import FidesUser
    from fides.api.models.manual_task.conditional_dependency import (
        ManualTaskConditionalDependency,
    )

# ------------------------------------------------------------
# Enums
# ------------------------------------------------------------


class ManualTaskExecutionTiming(str, Enum):
    """Enum for when a manual task should be executed in the privacy request DAG."""

    pre_execution = "pre_execution"  # Execute before the main DAG
    post_execution = "post_execution"  # Execute after the main DAG
    parallel = "parallel"  # Execute in parallel with the main DAG


class ManualTaskType(str, Enum):
    """Enum for manual task types."""

    privacy_request = "privacy_request"
    # Add more task types as needed


class ManualTaskParentEntityType(str, Enum):
    """Enum for manual task parent entity types."""

    connection_config = (
        "connection_config"  # used for access and erasure privacy requests
    )
    # Add more parent entity types as needed


class ManualTaskEntityType(str, Enum):
    """Enum for manual task entity types."""

    privacy_request = "privacy_request"
    # Add more entity types as needed


class ManualTaskReferenceType(str, Enum):
    """Enum for manual task reference types."""

    privacy_request = "privacy_request"
    connection_config = "connection_config"
    manual_task_config = "manual_task_config"
    assigned_user = "assigned_user"  # Reference to the user assigned to the task
    # Add more reference types as needed


class ManualTaskLogStatus(str, Enum):
    """Enum for manual task log status."""

    created = "created"
    updated = "updated"
    in_progress = "in_progress"
    complete = "complete"
    error = "error"
    retrying = "retrying"
    paused = "paused"
    awaiting_input = "awaiting_input"


class ManualTaskConfigurationType(str, Enum):
    """Enum for manual task configuration types."""

    access_privacy_request = "access_privacy_request"
    erasure_privacy_request = "erasure_privacy_request"
    # Add more configuration types as needed


class ManualTaskFieldType(str, Enum):
    """Enum for manual task field types."""

    text = "text"  # Key-value pairs
    checkbox = "checkbox"  # Boolean value
    attachment = "attachment"  # File upload
    # Add more field types as needed


class StatusType(str, Enum):
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


# ------------------------------------------------------------
# Schemas
# ------------------------------------------------------------


class ManualTaskFieldMetadata(FidesSchema):
    """Base schema for manual task field metadata."""

    label: Annotated[str, Field(description="Display label for the field")]
    required: Annotated[
        bool, Field(default=False, description="Whether the field is required")
    ]
    help_text: Annotated[
        Optional[str],
        Field(default=None, description="Help text to display with the field"),
    ]
    data_uses: Annotated[
        Optional[list[str]],
        Field(
            default=None,
            description="List of data uses associated with this field",
        ),
    ]

    model_config = ConfigDict(extra="allow")


# ------------------------------------------------------------
# Models
# ------------------------------------------------------------


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
        order_by="ManualTaskLog.created_at",
    )
    configs = relationship(
        "ManualTaskConfig",
        back_populates="task",
        uselist=True,
        viewonly=True,  # No cascade delete - configs are versioned
    )
    instances = relationship(
        "ManualTaskInstance",
        back_populates="task",
        uselist=True,
        viewonly=True,  # No cascade delete - instances contain historical data
    )
    submissions = relationship(
        "ManualTaskSubmission",
        back_populates="task",
        uselist=True,
        viewonly=True,  # No cascade delete - submissions are historical data
    )

    conditional_dependencies = relationship(
        "ManualTaskConditionalDependency",
        back_populates="task",
        uselist=True,
        cascade="all, delete-orphan",
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


class ManualTaskInstance(Base):
    """Model for tracking task status per entity instance."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "manual_task_instance"

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
        String,
        ForeignKey(
            "manual_task.id",
            name="manual_task_instance_task_id_fkey",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    config_id = Column(
        String,
        ForeignKey(
            "manual_task_config.id",
            name="manual_task_instance_config_id_fkey",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    # entity id is the entity that the instance relates to
    # (e.g. a privacy request is an entity that has its own manual task instance)
    entity_id = Column(String, nullable=False)
    entity_type = Column(EnumColumn(ManualTaskEntityType), nullable=False)
    # ignore[assignment] because the mypy and sqlalchemy types mismatch
    # upgrading to 2.0 allows mapping which provides better type safety visibility.
    status = Column(EnumColumn(StatusType), nullable=False, default=StatusType.pending)  # type: ignore[assignment]
    completed_at = Column(DateTime, nullable=True)  # type: ignore[assignment]
    completed_by_id = Column(String, nullable=True)  # type: ignore[assignment]
    due_date = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_manual_task_instance_completed_at", "completed_at"),
        Index("ix_manual_task_instance_config_id", "config_id"),
        Index("ix_manual_task_instance_entity", "entity_type", "entity_id"),
        Index("ix_manual_task_instance_entity_id", "entity_id"),
        Index("ix_manual_task_instance_entity_type", "entity_type"),
        Index("ix_manual_task_instance_status", "status"),
        Index("ix_manual_task_instance_task_id", "task_id"),
    )

    # Relationships
    task = relationship("ManualTask", back_populates="instances")
    config = relationship("ManualTaskConfig", back_populates="instances")
    submissions = relationship(
        "ManualTaskSubmission",
        back_populates="instance",
        uselist=True,
    )
    logs = relationship(
        "ManualTaskLog",
        back_populates="instance",
        primaryjoin="ManualTaskInstance.id == ManualTaskLog.instance_id",
        cascade="all, delete-orphan",
        order_by="ManualTaskLog.created_at",
        uselist=True,
    )
    attachments = relationship(
        "Attachment",
        secondary="attachment_reference",
        primaryjoin="and_(ManualTaskInstance.id == ManualTaskSubmission.instance_id, "
        "ManualTaskSubmission.id == AttachmentReference.reference_id, "
        "AttachmentReference.reference_type == 'manual_task_submission')",
        secondaryjoin="Attachment.id == AttachmentReference.attachment_id",
        order_by="Attachment.created_at",
        viewonly=True,
        uselist=True,
    )

    @property
    def required_fields(self) -> list["ManualTaskConfigField"]:
        """Get all required fields."""
        return [
            field
            for field in self.config.field_definitions
            if field.field_metadata.get("required", False)
        ]

    @property
    def incomplete_fields(self) -> list["ManualTaskConfigField"]:
        """Get all fields that have no submission.
        Returns:
            list[ManualTaskConfigField]: List of incomplete fields
        """
        return [
            field
            for field in self.config.field_definitions
            if not self.get_submission_for_field(field.id)
        ]

    @property
    def completed_fields(self) -> list["ManualTaskConfigField"]:
        """Get all fields that have been completed."""
        return [
            field
            for field in self.config.field_definitions
            if self.get_submission_for_field(field.id)
        ]

    def get_submission_for_field(
        self, field_id: str
    ) -> Optional["ManualTaskSubmission"]:
        """Get the submission for a specific field.

        Args:
            field_id: The ID of the field to get the submission for

        Returns:
            Optional[ManualTaskSubmission]: The submission for the field, or None if no submission exists
        """
        return next(
            (
                submission
                for submission in self.submissions
                if submission.field_id == field_id
            ),
            None,
        )

    def update_status(
        self, db: Session, new_status: StatusType, user_id: Optional[str] = None
    ) -> None:
        """Update the status with completion handling."""

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

    def delete(self, db: Session) -> None:
        """Delete the instance and all associated submissions with proper attachment cleanup."""
        # Delete submissions one by one to ensure proper attachment cleanup
        for submission in self.submissions:
            submission.delete(db)
        # Delete the instance itself
        db.delete(self)


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
    task = relationship("ManualTask", back_populates="references")


class ManualTaskConfig(Base):
    """Model for storing manual task configurations.
    A single configuration may have many fields of different types.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "manual_task_config"

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

    task_id = Column(
        String,
        ForeignKey(
            "manual_task.id",
            name="manual_task_config_task_id_fkey",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    config_type = Column(EnumColumn(ManualTaskConfigurationType), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)
    execution_timing = Column(
        EnumColumn(ManualTaskExecutionTiming),
        nullable=False,
        default=ManualTaskExecutionTiming.pre_execution,
    )

    __table_args__ = (
        Index("ix_manual_task_config_config_type", "config_type"),
        Index("ix_manual_task_config_task_id", "task_id"),
    )

    # Relationships
    task = relationship("ManualTask", back_populates="configs")
    instances = relationship(
        "ManualTaskInstance",
        back_populates="config",
        uselist=True,
        viewonly=True,
    )
    submissions = relationship(
        "ManualTaskSubmission",
        back_populates="config",
        uselist=True,
        viewonly=True,
    )
    field_definitions = relationship(
        "ManualTaskConfigField",
        back_populates="config",
        cascade="all, delete-orphan",
        uselist=True,
    )
    logs = relationship(
        "ManualTaskLog",
        back_populates="config",
        primaryjoin="ManualTaskConfig.id == ManualTaskLog.config_id",
        cascade="all, delete-orphan",
    )

    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = True
    ) -> "ManualTaskConfig":
        """Create a new manual task configuration."""
        # Validate config_type
        try:
            ManualTaskConfigurationType(data["config_type"])
        except ValueError:
            raise ValueError(f"Invalid config type: {data['config_type']}")

        config = super().create(db=db, data=data, check_name=check_name)

        # Log the config creation as a task-level log
        ManualTaskLog.create_log(
            db=db,
            task_id=data["task_id"],
            config_id=config.id,
            status=ManualTaskLogStatus.created,
            message=f"Created manual task configuration for {data['config_type']}",
            details={
                "config_type": data["config_type"],
            },
        )
        return config

    def get_field(self, field_key: str) -> Optional["ManualTaskConfigField"]:
        """Get a field by its key."""
        for field in self.field_definitions:
            if field.field_key == field_key:
                return field
        return None


class ManualTaskConfigField(Base):
    """Model for storing fields associated with each config."""

    @declared_attr
    def __tablename__(cls) -> str:
        return "manual_task_config_field"

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

    task_id = Column(
        String,
        ForeignKey(
            "manual_task.id",
            name="manual_task_config_field_task_id_fkey",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    config_id = Column(
        String,
        ForeignKey(
            "manual_task_config.id",
            name="manual_task_config_field_config_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    field_key = Column(String, nullable=False)
    field_type = Column(
        EnumColumn(ManualTaskFieldType), nullable=False
    )  # Using ManualTaskFieldType
    field_metadata: dict[str, Any] = cast(
        dict[str, Any], Column(JSONB, nullable=False, default={})
    )

    __table_args__ = (
        UniqueConstraint("config_id", "field_key", name="unique_field_key_per_config"),
        Index("ix_manual_task_config_field_config_id", "config_id"),
        Index("ix_manual_task_config_field_field_key", "field_key"),
        Index("ix_manual_task_config_field_task_id", "task_id"),
    )

    # Relationships
    config = relationship("ManualTaskConfig", back_populates="field_definitions")
    submissions = relationship(
        "ManualTaskSubmission",
        back_populates="field",
        uselist=True,
    )

    @property
    def field_metadata_model(self) -> ManualTaskFieldMetadata:
        """Get the field metadata as a Pydantic model."""
        assert isinstance(
            self.field_metadata, dict
        ), "field_metadata must be a dictionary"
        return ManualTaskFieldMetadata.model_validate(self.field_metadata)

    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = True
    ) -> "ManualTaskConfigField":
        """Create a new manual task config field."""
        # Get the config to access its task_id and check if it exists
        config = (
            db.query(ManualTaskConfig)
            .filter(ManualTaskConfig.id == data["config_id"])
            .first()
        )
        if not config:
            raise ValueError(f"Config with id {data['config_id']} not found")

        # Create the field and let SQLAlchemy complex type validation handled in service.
        field = super().create(db=db, data=data, check_name=check_name)

        # Create a log entry
        if config.task_id:
            ManualTaskLog.create_log(
                db=db,
                task_id=config.task_id,
                config_id=data["config_id"],
                status=ManualTaskLogStatus.created,
                message=f"Created manual task config field for {data['field_key']}",
            )
        return field


class ManualTaskSubmission(Base):
    """Model for storing user submissions.
    Each submission represents data for a single field.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "manual_task_submission"

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
        String,
        ForeignKey(
            "manual_task.id",
            name="manual_task_submission_task_id_fkey",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    config_id = Column(
        String,
        ForeignKey(
            "manual_task_config.id",
            name="manual_task_submission_config_id_fkey",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    field_id = Column(
        String,
        ForeignKey(
            "manual_task_config_field.id",
            name="manual_task_submission_field_id_fkey",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    instance_id = Column(
        String,
        ForeignKey(
            "manual_task_instance.id",
            name="manual_task_submission_instance_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    submitted_by = Column(
        String,
        ForeignKey(
            "fidesuser.id",
            name="manual_task_submission_submitted_by_fkey",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    submitted_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    data = Column(JSONB, nullable=False)

    __table_args__ = (
        Index("ix_manual_task_submission_config_id", "config_id"),
        Index("ix_manual_task_submission_field_id", "field_id"),
        Index("ix_manual_task_submission_instance_field", "instance_id", "field_id"),
        Index("ix_manual_task_submission_instance_id", "instance_id"),
        Index("ix_manual_task_submission_submitted_at", "submitted_at"),
        Index("ix_manual_task_submission_submitted_by", "submitted_by"),
        Index("ix_manual_task_submission_task_id", "task_id"),
    )

    # Relationships
    task = relationship("ManualTask", back_populates="submissions")
    config = relationship("ManualTaskConfig", back_populates="submissions")
    field = relationship("ManualTaskConfigField", back_populates="submissions")
    instance = relationship(
        "ManualTaskInstance",
        back_populates="submissions",
    )
    attachments = relationship(
        "Attachment",
        secondary="attachment_reference",
        primaryjoin="and_(ManualTaskSubmission.id == AttachmentReference.reference_id, "
        "AttachmentReference.reference_type == 'manual_task_submission')",
        secondaryjoin="Attachment.id == AttachmentReference.attachment_id",
        order_by="Attachment.created_at",
        uselist=True,
        viewonly=True,  # Make read-only to avoid overlapping relationship warnings
    )

    user = relationship(
        "FidesUser",
        primaryjoin="FidesUser.id == ManualTaskSubmission.submitted_by",
        viewonly=True,
    )

    def delete(self, db: Session) -> None:
        """Delete the submission and all associated attachments."""
        from fides.api.models.attachment import Attachment, AttachmentReferenceType

        # Delete attachments associated with this submission
        Attachment.delete_attachments_for_reference_and_type(
            db, self.id, AttachmentReferenceType.manual_task_submission
        )
        # Delete the submission itself
        db.delete(self)

    @staticmethod
    def delete_submissions_for_instance(db: Session, instance_id: str) -> None:
        """
        Deletes submissions associated with a given instance_id.
        Properly handles attachment cleanup for each submission.

        Args:
            db: Database session.
            instance_id: The instance id to delete submissions for.

        Example:
          - Delete all submissions associated with a manual task instance.
            ``ManualTaskSubmission.delete_submissions_for_instance(
                db, instance.id
            )``
        """
        # Query submissions explicitly to avoid lazy loading
        submissions = (
            db.query(ManualTaskSubmission)
            .filter(ManualTaskSubmission.instance_id == instance_id)
            .all()
        )

        for submission in submissions:
            submission.delete(db)


class ManualTaskLog(Base):
    """Model for storing manual task execution logs."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "manual_task_log"

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

    task_id = Column(
        String, ForeignKey("manual_task.id", ondelete="SET NULL"), nullable=True
    )
    config_id = Column(
        String, ForeignKey("manual_task_config.id", ondelete="CASCADE"), nullable=True
    )
    instance_id = Column(
        String,
        ForeignKey("manual_task_instance.id", ondelete="CASCADE"),
        nullable=True,
    )
    # The user responsible for the action being logged.  This may be `None`
    # for system-initiated events or for legacy records created before this
    # column existed.
    user_id = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False)
    message = Column(String, nullable=True)
    details = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_manual_task_log_config_id", "config_id"),
        Index("ix_manual_task_log_created_at", "created_at"),
        Index("ix_manual_task_log_instance_id", "instance_id"),
        Index("ix_manual_task_log_status", "status"),
        Index("ix_manual_task_log_task_id", "task_id"),
        Index("ix_manual_task_log_user_id", "user_id"),
    )

    # Relationships
    task = relationship("ManualTask", back_populates="logs", foreign_keys=[task_id])
    config = relationship(
        "ManualTaskConfig",
        back_populates="logs",
        foreign_keys=[config_id],
    )
    instance = relationship("ManualTaskInstance", back_populates="logs")

    @classmethod
    def create_log(
        cls,
        db: Session,
        task_id: str,
        status: "ManualTaskLogStatus",
        message: str,
        user_id: Optional[str] = None,
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
            "user_id": user_id or get_user_id(),
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
        user_id: Optional[str] = None,
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
            user_id=user_id or get_user_id(),
            message=message,
            details=details,
        )
