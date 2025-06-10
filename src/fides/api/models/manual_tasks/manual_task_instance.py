from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Integer
from sqlalchemy.orm import Session, relationship
from sqlalchemy.dialects.postgresql import JSONB

from fides.api.db.base_class import Base
from fides.api.models.attachment import Attachment, AttachmentReference
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskSubmission,
)
from fides.api.models.manual_tasks.manual_task_log import (
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import StatusTransitionMixin, StatusType


class ManualTaskInstance(Base, StatusTransitionMixin[StatusType]):
    """Model for tracking task status per entity instance."""

    __tablename__ = "manual_task_instance"

    # Database columns
    task_id = Column(String, ForeignKey("manual_task.id"), nullable=False)
    config_id = Column(String, ForeignKey("manual_task_config.id"), nullable=False)
    entity_id = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default=StatusType.pending)
    completed_at = Column(DateTime, nullable=True)
    completed_by_id = Column(String, nullable=True)

    # Relationships
    task = relationship("ManualTask", back_populates="instances")
    config = relationship("ManualTaskConfig", back_populates="instances")
    submissions = relationship(
        "ManualTaskSubmission", back_populates="instance", cascade="all, delete-orphan"
    )
    logs = relationship(
        "ManualTaskLog",
        back_populates="instance",
        primaryjoin="ManualTaskInstance.id == ManualTaskLog.instance_id",
        viewonly=True,
        order_by="ManualTaskLog.created_at",
    )

    @property
    def attachments(self, db: Session) -> list["Attachment"]:
        """Get all attachments associated with this task instance.
        This includes attachments from all submissions for this instance.
        Args:
            db: Database session
        Returns:
            list[Attachment]: List of attachments associated with this instance
        """
        # Get all submissions for this instance
        submissions = self.submissions

        # Get all attachment references for these submissions
        attachment_refs = (
            db.query(AttachmentReference)
            .filter(
                AttachmentReference.reference_id.in_([s.id for s in submissions]),
                AttachmentReference.reference_type == "manual_task_submission",
            )
            .all()
        )

        # Get the actual attachments
        attachments = (
            db.query(Attachment)
            .filter(Attachment.id.in_([ref.attachment_id for ref in attachment_refs]))
            .all()
        )

        return attachments

    @property
    def required_fields(self) -> list["ManualTaskConfigField"]:
        """Get all required fields."""
        return [field for field in self.config.field_definitions if field.required]

    @property
    def incomplete_fields(self) -> list["ManualTaskConfigField"]:
        """Get all fields that haven't been completed yet.
        A field is considered incomplete if:
        1. It's required and has no submission
        Returns:
            list[ManualTaskConfigField]: List of incomplete fields
        """
        return [field for field in self.required_fields if not self.get_submission_for_field(field.id)]

    @property
    def completed_fields(self) -> list["ManualTaskConfigField"]:
        """Get all fields that have been completed."""
        return [field for field in self.config.field_definitions if field.required and self.get_submission_for_field(field.id)]

    # CRUD Operations
    @classmethod
    def create(
        cls,
        db: Session,
        data: dict[str, Any],
    ) -> "ManualTaskInstance":
        """Create a new task instance for an entity.
        Args:
            db: Database session
            data: Dictionary containing task_id, config_id, entity_id, and entity_type
        """
        return super().create(db=db, data=data)



class ManualTaskSubmission(Base):
    """Model for storing user submissions.
    Each submission represents data for a single field.
    """

    __tablename__ = "manual_task_submission"
    task_id = Column(String, ForeignKey("manual_task.id"))
    config_id = Column(String, ForeignKey("manual_task_config.id"))
    field_id = Column(String, ForeignKey("manual_task_config_field.id"))
    instance_id = Column(String, ForeignKey("manual_task_instance.id"), nullable=True)
    submitted_by = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, default=datetime.now(timezone.utc))
    data = Column(JSONB, nullable=False)

    # Relationships
    task = relationship("ManualTask", back_populates="submissions")
    config = relationship("ManualTaskConfig", back_populates="submissions")
    field = relationship("ManualTaskConfigField", back_populates="submissions")
    instance = relationship("ManualTaskInstance", back_populates="submissions")

    # 3. CRUD Operations
    @classmethod
    def create(
        cls, db: Session, data: dict[str, Any], check_name: Optional[bool]
    ) -> None:
        """Create a new submission for a single field."""
        return super().create(db=db, data=data, check_name=check_name)

    @classmethod
    def update(
        cls, db: Session, *, data: dict[str, Any], check_name: Optional[bool] = True
    ) -> "ManualTaskSubmission":
        """Create or update a submission for a single field."""
        return super().create_or_update(db=db, data=data, check_name=check_name)
