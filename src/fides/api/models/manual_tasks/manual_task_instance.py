from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, cast

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfigField
from fides.api.schemas.manual_tasks.manual_task_status import (
    StatusTransitionMixin,
    StatusType,
)

if TYPE_CHECKING:  # pragma: no cover
    from fides.api.models.attachment import Attachment  # pragma: no cover
    from fides.api.models.fides_user import FidesUser  # pragma: no cover
    from fides.api.models.manual_tasks.manual_task import ManualTask  # pragma: no cover
    from fides.api.models.manual_tasks.manual_task_config import (
        ManualTaskConfig,  # pragma: no cover
    )
    from fides.api.models.manual_tasks.manual_task_log import (
        ManualTaskLog,  # pragma: no cover; pragma: no cover
    )


class ManualTaskInstance(Base, StatusTransitionMixin):
    """Model for tracking task status per entity instance."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "manual_task_instance"

    # Database columns
    task_id = Column(String, ForeignKey("manual_task.id"), nullable=False)
    config_id = Column(String, ForeignKey("manual_task_config.id"), nullable=False)
    # entity id is the entity that the instance is for (e.g. privacy request)
    # TODO: Add to schemas
    entity_id = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    status: StatusType = cast(
        StatusType, Column(String, nullable=False, default=StatusType.pending)
    )
    due_date: Optional[datetime] = cast(
        Optional[datetime], Column(DateTime, nullable=True)
    )
    completed_at: Optional[datetime] = cast(
        Optional[datetime], Column(DateTime, nullable=True)
    )
    completed_by_id: Optional[str] = cast(Optional[str], Column(String, nullable=True))

    # Relationships
    task = relationship("ManualTask", back_populates="instances")
    config = relationship("ManualTaskConfig", back_populates="instances")
    submissions = relationship(
        "ManualTaskSubmission",
        back_populates="instance",
        cascade="all, delete-orphan",
        uselist=True,
    )
    logs = relationship(
        "ManualTaskLog",
        back_populates="instance",
        primaryjoin="ManualTaskInstance.id == ManualTaskLog.instance_id",
        viewonly=True,
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
        """Get all fields that haven't been completed yet.
        A field is considered incomplete if:
        1. It's required and has no submission
        Returns:
            list[ManualTaskConfigField]: List of incomplete fields
        """
        return [
            field
            for field in self.required_fields
            if not self.get_submission_for_field(field.id)
        ]

    @property
    def completed_fields(self) -> list["ManualTaskConfigField"]:
        """Get all fields that have been completed."""
        return [
            field
            for field in self.config.field_definitions
            if field.field_metadata.get("required", False)
            and self.get_submission_for_field(field.id)
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


class ManualTaskSubmission(Base):
    """Model for storing user submissions.
    Each submission represents data for a single field.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "manual_task_submission"

    # Database columns
    task_id = Column(String, ForeignKey("manual_task.id"))
    config_id = Column(String, ForeignKey("manual_task_config.id"))
    field_id = Column(String, ForeignKey("manual_task_config_field.id"))
    instance_id = Column(String, ForeignKey("manual_task_instance.id"), nullable=False)
    submitted_by = Column(String, ForeignKey("fidesuser.id"), nullable=True)
    submitted_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    data = Column(JSONB, nullable=False)

    # Relationships
    task = relationship("ManualTask", back_populates="submissions", viewonly=True)
    config = relationship(
        "ManualTaskConfig", back_populates="submissions", viewonly=True
    )
    field = relationship(
        "ManualTaskConfigField", back_populates="submissions", viewonly=True
    )
    instance = relationship(
        "ManualTaskInstance", back_populates="submissions", viewonly=True
    )
    attachments = relationship(
        "Attachment",
        secondary="attachment_reference",
        primaryjoin="and_(ManualTaskSubmission.id == AttachmentReference.reference_id, "
        "AttachmentReference.reference_type == 'manual_task_submission')",
        secondaryjoin="Attachment.id == AttachmentReference.attachment_id",
        order_by="Attachment.created_at",
        viewonly=True,
        uselist=True,
    )

    user = relationship(
        "FidesUser",
        primaryjoin="FidesUser.id == ManualTaskSubmission.submitted_by",
        viewonly=True,
    )
