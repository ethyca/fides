from typing import Any, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import Session, relationship

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
from fides.api.models.manual_tasks.status import StatusTransitionMixin, StatusType
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskReferenceType,
    ManualTaskType,
)


def _check_instance_status(db: Session, instance_id: str, **kwargs) -> None:
    """Check if an instance is completed and log it."""
    instance = db.query(ManualTaskInstance).filter_by(id=instance_id).first()
    if instance and instance.status == StatusType.completed:
        ManualTaskLog.create_log(
            db=db,
            task_id=instance.task_id,
            config_id=instance.config_id,
            instance_id=instance.id,
            status=ManualTaskLogStatus.awaiting_input,
            message="Task instance already completed",
            details=kwargs,
        )


class ManualTask(Base):
    """Model for storing manual tasks.

    This model can be used for both privacy request tasks and general tasks.
    For privacy requests, it replaces the functionality of manual webhooks.
    For other use cases, it provides a flexible task management system.
    """

    __tablename__ = "manual_task"

    # Database columns
    task_type = Column(String, nullable=False, default=ManualTaskType.privacy_request)
    parent_entity_id = Column(String, nullable=False)
    parent_entity_type = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=True)

    # Relationships
    references = relationship("ManualTaskReference", back_populates="task")
    configs = relationship(
        "ManualTaskConfig",
        secondary="manual_task_reference",
        primaryjoin="and_(ManualTask.id == ManualTaskReference.task_id, ManualTaskReference.reference_type == 'manual_task_config')",
        secondaryjoin="ManualTaskConfig.id == ManualTaskReference.reference_id",
        viewonly=True,
    )
    submissions = relationship("ManualTaskSubmission", back_populates="task")
    logs = relationship(
        "ManualTaskLog",
        back_populates="task",
        primaryjoin="and_(ManualTask.id == ManualTaskLog.task_id, ManualTaskLog.instance_id.is_(None))",
        viewonly=True,
        order_by="ManualTaskLog.created_at",
    )
    instances = relationship("ManualTaskInstance", back_populates="task")
    field_definitions = relationship("ManualTaskConfigField", back_populates="task")

    # Properties
    @property
    def assigned_users(self) -> list[str]:
        """Get all users assigned to this task."""
        return [
            ref.reference_id
            for ref in self.references
            if ref.reference_type == ManualTaskReferenceType.assigned_user
        ]

    # CRUD Operations
    @classmethod
    def create(cls, db: Session, data: dict[str, Any]) -> "ManualTask":
        """Create a new manual task."""
        task = super().create(db=db, data=data, check_name=False)
        ManualTaskLog.create_log(
            db=db,
            task_id=task.id,
            status=ManualTaskLogStatus.complete,
            message=f"Created manual task for {data['task_type']}",
        )
        return task

    # Instance Management
    def get_entity_instances(self, entity_type: str) -> list["ManualTaskInstance"]:
        """Get all instances for a specific entity type.

        Args:
            entity_type: Type of entity to get instances for
        """
        return [
            instance
            for instance in self.instances
            if instance.entity_type == entity_type
        ]

    def get_instance_for_entity(
        self, entity_id: str, entity_type: str
    ) -> Optional["ManualTaskInstance"]:
        """Get the task instance for a specific entity.

        Args:
            entity_id: ID of the entity
            entity_type: Type of the entity
        """
        for instance in self.instances:
            if instance.entity_id == entity_id and instance.entity_type == entity_type:
                return instance
        return None

    def create_entity_instance(
        self,
        db: Session,
        config_id: str,
        entity_id: str,
        entity_type: str,
    ) -> "ManualTaskInstance":
        """Create a new task instance for an entity.

        Args:
            db: Database session
            config_id: ID of the configuration to use
            entity_id: ID of the entity
            entity_type: Type of the entity

        Raises:
            ValueError: If an instance already exists for this entity or if the config is not found
        """
        # Check if the config exists
        config = ManualTaskConfig.get_by_id(db, self.id, config_id)
        if not config:
            raise ValueError("Configuration not found")

        # Check if an instance already exists for this entity
        existing_instance = self.get_instance_for_entity(entity_id, entity_type)
        if existing_instance:
            raise ValueError("Instance already exists for this entity")

        # Create the instance
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": self.id,
                "config_id": config_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
            },
        )

        # Create a reference to the entity
        ref = ManualTaskReference(
            task_id=self.id, reference_id=entity_id, reference_type=entity_type
        )
        db.add(ref)
        db.commit()

        return instance

    # User Management
    def assign_user(self, db: Session, user_id: str) -> None:
        """Assign a user to this task. This assumes there is a single user assigned to the task.

        Args:
            db: Database session
            user_id: ID of the user to assign

        Raises:
            ValueError: If user_id is None or empty
        """
        if not user_id:
            raise ValueError("User ID is required for assignment")

        # Remove any existing user assignment
        for ref in self.references:
            if ref.reference_type == ManualTaskReferenceType.assigned_user:
                db.delete(ref)
                break

        # Create new user assignment
        ref = ManualTaskReference(
            task_id=self.id,
            reference_id=user_id,
            reference_type=ManualTaskReferenceType.assigned_user,
        )
        db.add(ref)
        db.commit()

        # Log the user assignment
        ManualTaskLog.create_log(
            db=db,
            task_id=self.id,
            status=ManualTaskLogStatus.complete,
            message=f"User {user_id} assigned to task",
            details={"assigned_user_id": user_id},
        )

    def unassign_user(self, db: Session) -> None:
        """Remove the user assignment from this task.

        Args:
            db: Database session
        """
        for ref in self.references:
            if ref.reference_type == ManualTaskReferenceType.assigned_user:
                user_id = ref.reference_id
                db.delete(ref)
                db.commit()

                # Log the user unassignment
                ManualTaskLog.create_log(
                    db=db,
                    task_id=self.id,
                    status=ManualTaskLogStatus.complete,
                    message=f"User {user_id} unassigned from task",
                    details={"unassigned_user_id": user_id},
                )
                break


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

    @classmethod
    def is_instance_completed(cls, db: Session, instance_id: str) -> bool:
        """Check if an instance is completed.

        Args:
            db: Database session
            instance_id: ID of the instance to check

        Returns:
            bool: True if the instance is completed, False otherwise
        """
        instance = db.query(cls).filter_by(id=instance_id).first()
        return instance is not None and instance.status == StatusType.completed

    def log_completed_status(
        self, db: Session, field_key: str, field_type: str, submitted_by: int
    ) -> None:
        """Log that this instance is completed.

        Args:
            db: Database session
            field_key: Key of the field being submitted
            field_type: Type of the field being submitted
            submitted_by: ID of the user submitting
        """
        if self.status == StatusType.completed:
            ManualTaskLog.create_log(
                db=db,
                task_id=self.task_id,
                config_id=self.config_id,
                instance_id=self.id,
                status=ManualTaskLogStatus.error,
                message="Cannot submit to a completed task instance",
                details={
                    "field_key": field_key,
                    "field_type": field_type,
                    "submitted_by": submitted_by,
                },
            )

    def get_submission_for_field(
        self, field_id: str
    ) -> Optional["ManualTaskSubmission"]:
        """Get the submission for a specific field.

        Args:
            field_id: ID of the field to get submission for

        Returns:
            Optional[ManualTaskSubmission]: The submission if it exists
        """
        return next((s for s in self.submissions if s.field_id == field_id), None)

    def get_incomplete_fields(self) -> list["ManualTaskConfigField"]:
        """Get all fields that haven't been completed yet.

        A field is considered incomplete if:
        1. It's required and has no submission

        Returns:
            list[ManualTaskConfigField]: List of incomplete fields
        """
        incomplete_fields = []

        for field in self.config.field_definitions:
            # Find the submission for this field
            submission = self.get_submission_for_field(field.id)

            # Field is incomplete if:
            # 1. It's required and has no submission
            if field.required and not submission:
                incomplete_fields.append(field)

        return incomplete_fields

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
        instance = super().create(
            db=db,
            data=data,
        )
        # Log instance creation (instance-level log)
        ManualTaskLog.create_log(
            db=db,
            task_id=data["task_id"],
            config_id=data["config_id"],
            instance_id=instance.id,
            status=ManualTaskLogStatus.complete,
            message=f"Created task instance for {data['entity_type']} {data['entity_id']}",
            details={
                "entity_type": data["entity_type"],
                "entity_id": data["entity_id"],
                "initial_status": StatusType.pending,
            },
        )
        return instance

    # Status Management
    def update_status(
        self, db: Session, new_status: StatusType, user_id: Optional[str] = None
    ) -> None:
        """Override update_status to add logging."""
        previous_status = self.status
        super().update_status(db, new_status, user_id)

        # Only create a log if the status actually changed
        if previous_status != new_status:
            # Create a log entry for the status transition
            ManualTaskLog.create_log(
                db=db,
                task_id=self.task_id,
                config_id=self.config_id,
                instance_id=self.id,
                status=ManualTaskLogStatus.in_processing,
                message=f"Task instance status transitioning from {previous_status} to {new_status}",
                details={
                    "previous_status": previous_status,
                    "new_status": new_status,
                    "user_id": user_id,
                },
            )

    def update_status_from_submissions(self, db: Session) -> None:
        """Update the instance status based on the status of all submissions.

        Each submission represents data for a single field. The status is updated based on:
        - Whether all required fields have valid submissions
        - Whether any fields have valid submissions

        Args:
            db: Database session
        """
        if not self.submissions:
            return

        # Get all required fields
        required_fields = [
            field for field in self.config.field_definitions if field.required
        ]

        # Check if all required fields have valid submissions
        all_fields_valid = True
        for field in required_fields:
            # Find the submission for this field
            submission = next(
                (s for s in self.submissions if s.field_id == field.id),
                None,
            )
            if not submission:
                all_fields_valid = False
                break

        # Check if any fields have submissions
        any_fields = len(self.submissions) > 0

        previous_status = self.status

        # Update status based on field submissions
        if self.status == StatusType.pending and any_fields:
            # First transition to in_progress if we have any submissions
            self.update_status(db, StatusType.in_progress)
            # If all fields are valid, immediately transition to completed
            if all_fields_valid:
                self.update_status(db, StatusType.completed)
        elif self.status == StatusType.in_progress and all_fields_valid:
            # If we're already in_progress and all fields are valid, complete the task
            self.update_status(db, StatusType.completed)
        elif not any_fields and self.status != StatusType.pending:
            # Only go back to pending if we have no valid submissions
            self.update_status(db, StatusType.pending)

        # Log the status update
        ManualTaskLog.create_log(
            db=db,
            task_id=self.task_id,
            config_id=self.config_id,
            instance_id=self.id,
            status=ManualTaskLogStatus.complete,
            message=f"Updated task instance status to {self.status} based on submissions",
            details={
                "previous_status": previous_status,
                "submission_count": len(self.submissions),
                "all_fields_valid": all_fields_valid,
                "any_fields": any_fields,
            },
        )

    # Data Access Methods
    def get_all_logs(self) -> list["ManualTaskLog"]:
        """Get all logs for this instance.

        Returns:
            list[ManualTaskLog]: List of all logs for this instance
        """
        return self.logs

    def get_attachments(self, db: Session) -> list["Attachment"]:
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

    def get_submissions(self) -> list["ManualTaskSubmission"]:
        """Get all submissions for this instance."""
        return self.submissions


class ManualTaskReference(Base):
    """Join table to associate manual tasks with multiple references.

    A single task may have many references including privacy requests, configurations, and assigned users.
    """

    __tablename__ = "manual_task_reference"

    # Database columns
    task_id = Column(String, ForeignKey("manual_task.id"))
    reference_id = Column(String)
    reference_type = Column(String, nullable=False)

    # Relationships
    task = relationship("ManualTask", back_populates="references")
