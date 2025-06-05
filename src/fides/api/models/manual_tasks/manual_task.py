from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.attachment import Attachment, AttachmentReference
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
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


class ManualTaskInstance(Base, StatusTransitionMixin[StatusType]):
    """Model for tracking task status per entity instance."""

    __tablename__ = "manual_task_instance"

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
    submissions = relationship("ManualTaskSubmission", back_populates="instance")
    logs = relationship(
        "ManualTaskLog",
        back_populates="instance",
        primaryjoin="ManualTaskInstance.id == ManualTaskLog.instance_id",
        viewonly=True,
        order_by="ManualTaskLog.created_at",
    )

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

    def get_incomplete_fields(self) -> list["ManualTaskConfigField"]:
        """Get all fields that haven't been completed yet.

        A field is considered incomplete if:
        1. It's required and has no submission
        2. It has a submission but the submission is not complete

        Returns:
            List[ManualTaskConfigField]: List of incomplete fields
        """
        incomplete_fields = []

        for field in self.config.field_definitions:
            # Find the submission for this field if it exists
            submission = next(
                (s for s in self.submissions if s.field_id == field.id), None
            )

            # Field is incomplete if:
            # 1. It's required and has no submission
            # 2. It has a submission that's not complete
            if (field.required and not submission) or (
                submission and submission.status != StatusType.completed
            ):
                incomplete_fields.append(field)

        return incomplete_fields

    def update_status_from_submissions(self, db: Session) -> None:
        """Update the instance status based on the status of all submissions.

        If all submissions are complete and all required fields have valid data,
        updates status to completed.
        If some submissions are complete, updates status to in_progress.
        If no submissions are complete, keeps status as pending.

        Args:
            db: Database session
        """
        if not self.submissions:
            return

        # Get all required fields
        required_fields = [
            field for field in self.config.field_definitions if field.required
        ]

        # Check if all required fields have valid data
        all_fields_valid = True
        for field in required_fields:
            # Find the submission for this field
            submission = next(
                (s for s in self.submissions if s.field_id == field.id), None
            )

            # Field is invalid if:
            # 1. No submission exists
            # 2. Submission exists but is not complete
            # 3. Submission exists and is complete but data is invalid
            if not submission or submission.status != StatusType.completed:
                all_fields_valid = False
                break

            # Validate the field data
            if not field.validate_field_data(submission.data.get(field.field_key)):
                all_fields_valid = False
                break

        all_complete = all(
            submission.status == StatusType.completed for submission in self.submissions
        )
        some_complete = any(
            submission.status == StatusType.completed for submission in self.submissions
        )

        previous_status = self.status

        # Only attempt transitions if we're not already in the target state
        if all_complete and all_fields_valid and self.status != StatusType.completed:
            # Must transition through in_progress first
            if self.status == StatusType.pending:
                self.update_status(db, StatusType.in_progress)
            self.update_status(db, StatusType.completed)
        elif (
            some_complete or len(self.submissions) > 0
        ) and self.status == StatusType.pending:
            # Update to in_progress if we have any submissions or some are complete
            self.update_status(db, StatusType.in_progress)
        elif (
            not some_complete
            and len(self.submissions) == 0
            and self.status != StatusType.pending
        ):
            # Only go back to pending if we have no submissions
            self.update_status(db, StatusType.pending)

        # Log the status update (instance-level log)
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
                "complete_count": sum(
                    1 for s in self.submissions if s.status == StatusType.completed
                ),
                "all_fields_valid": all_fields_valid,
            },
        )

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

    def get_submissions(self) -> list["ManualTaskSubmission"]:
        """Get all submissions for this instance."""
        return self.submissions

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


class ManualTask(Base):
    """Model for storing manual tasks.

    This model can be used for both privacy request tasks and general tasks.
    For privacy requests, it replaces the functionality of manual webhooks.
    For other use cases, it provides a flexible task management system.
    """

    __tablename__ = "manual_task"

    task_type = Column(String, nullable=False, default=ManualTaskType.privacy_request)
    parent_entity_id = Column(String, nullable=False)
    parent_entity_type = Column(
        String, nullable=False
    )  # Using ManualTaskParentEntityType
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

    def get_entity_instances(self, entity_type: str) -> list[ManualTaskInstance]:
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
    ) -> Optional[ManualTaskInstance]:
        """Get the task instance for a specific entity.

        Args:
            entity_id: ID of the entity
            entity_type: Type of the entity
        """
        for instance in self.instances:
            if instance.entity_id == entity_id and instance.entity_type == entity_type:
                return instance
        return None

    def create_manual_task_config(
        self,
        db: Session,
        config_type: str,
        fields: list[Optional[dict[str, Any]]],
    ) -> "ManualTaskConfig":
        """Create a new manual task configuration."""
        config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": self.id,
                "config_type": config_type,
                "fields": fields,
            },
        )
        ManualTaskLog.create_log(
            db=db,
            task_id=self.id,
            config_id=config.id,
            status=ManualTaskLogStatus.complete,
            message=f"Created manual task configuration for {config_type}",
        )
        return config

    def create_entity_instance(
        self,
        db: Session,
        config_id: str,
        entity_id: str,
        entity_type: str,
    ) -> ManualTaskInstance:
        """Create a new task instance for an entity.

        Args:
            db: Database session
            config_id: ID of the configuration to use
            entity_id: ID of the entity
            entity_type: Type of the entity
        """
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

    def get_assigned_user(self) -> Optional[str]:
        """Get the user ID assigned to this task."""
        for ref in self.references:
            if ref.reference_type == ManualTaskReferenceType.assigned_user:
                return ref.reference_id
        return None

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


class ManualTaskReference(Base):
    """Join table to associate manual tasks with multiple references.

    A single task may have many references including privacy requests, configurations, and assigned users.
    """

    __tablename__ = "manual_task_reference"

    task_id = Column(String, ForeignKey("manual_task.id"))
    reference_id = Column(String)
    reference_type = Column(String, nullable=False)

    # Relationships
    task = relationship("ManualTask", back_populates="references")


class ManualTaskSubmission(Base, StatusTransitionMixin[StatusType]):
    """Model for storing user submissions."""

    __tablename__ = "manual_task_submission"

    task_id = Column(String, ForeignKey("manual_task.id"))
    config_id = Column(String, ForeignKey("manual_task_config.id"))
    field_id = Column(String, ForeignKey("manual_task_config_field.id"))
    instance_id = Column(String, ForeignKey("manual_task_instance.id"), nullable=True)
    submitted_by = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, default=datetime.now(timezone.utc))
    data = Column(JSONB, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    completed_by_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default=StatusType.in_progress)

    # Relationships
    task = relationship("ManualTask", back_populates="submissions")
    config = relationship("ManualTaskConfig", back_populates="submissions")
    field = relationship("ManualTaskConfigField", back_populates="submissions")
    instance = relationship("ManualTaskInstance", back_populates="submissions")

    @classmethod
    def create(
        cls, db: Session, data: dict[str, Any], check_name: Optional[bool]
    ) -> None:
        """We want to use create or update, but we want to use create for now."""
        config = ManualTaskConfig.get_by_key_or_id(
            db=db, data={"id": data["config_id"]}
        )
        if not config.validate_submission(data["data"], field_id=data["field_id"]):
            raise ValueError("Invalid submission data")

        return super().create(db=db, data=data, check_name=check_name)

    @classmethod
    def create_or_update(
        cls, db: Session, *, data: dict[str, Any], check_name: Optional[bool] = True
    ) -> "ManualTaskSubmission":
        """Create or update a manual task submission."""
        # Validate the submission data
        config = ManualTaskConfig.get_by_key_or_id(
            db=db, data={"id": data["config_id"]}
        )
        if not config.validate_submission(data["data"], field_id=data["field_id"]):
            # Create error log before raising exception
            ManualTaskLog.create_log(
                db=db,
                task_id=data["task_id"],
                config_id=data["config_id"],
                instance_id=data.get("instance_id"),
                status=ManualTaskLogStatus.error,
                message="Invalid submission data",
                details={
                    "field_id": data["field_id"],
                    "submitted_data": data["data"],
                },
            )
            raise ValueError("Invalid submission data")

        submission = super().create_or_update(db=db, data=data, check_name=check_name)

        # Log submission creation/update (instance-level log)
        ManualTaskLog.create_log(
            db=db,
            task_id=data["task_id"],
            config_id=data["config_id"],
            instance_id=data["instance_id"],
            status=ManualTaskLogStatus.complete,
            message=f"{'Updated' if submission.id else 'Created'} submission for field {submission.field.field_key}",
            details={
                "field_key": submission.field.field_key,
                "field_type": submission.field.field_type,
                "submitted_by": data["submitted_by"],
                "status": submission.status,
            },
        )

        # If the submission is valid, automatically complete it
        if submission.field.validate_field_data(
            submission.data.get(submission.field.field_key)
        ):
            submission.complete(db, str(data["submitted_by"]))

        # Update instance status based on submissions
        if submission.instance:
            submission.instance.update_status_from_submissions(db)

        return submission

    def complete(self, db: Session, completed_by_id: str) -> None:
        """Mark a submission as complete.

        Args:
            db: Database session
            completed_by_id: ID of the user completing the submission

        Raises:
            ValueError: If completed_by_id is None or empty
        """
        if not completed_by_id:
            raise ValueError("User ID is required for completion")

        # If already completed, log and return
        if self.status == StatusType.completed:
            ManualTaskLog.create_log(
                db=db,
                task_id=self.task_id,
                config_id=self.config_id,
                instance_id=self.instance_id,
                status=ManualTaskLogStatus.awaiting_input,
                message=f"Submission for field {self.field.field_key} already completed",
                details={
                    "field_key": self.field.field_key,
                    "field_type": self.field.field_type,
                    "completed_by": completed_by_id,
                },
            )
            return

        # Use StatusTransitionMixin to update status and handle completion metadata
        self.update_status(db, StatusType.completed, completed_by_id)

        # Log submission completion (instance-level log)
        ManualTaskLog.create_log(
            db=db,
            task_id=self.task_id,
            config_id=self.config_id,
            instance_id=self.instance_id,
            status=ManualTaskLogStatus.complete,
            message=f"Completed submission for field {self.field.field_key}",
            details={
                "field_key": self.field.field_key,
                "field_type": self.field.field_type,
                "completed_by": completed_by_id,
                "completion_time": self.completed_at.isoformat(),
            },
        )

        # Update instance status based on all submissions
        if self.instance:
            self.instance.update_status_from_submissions(db)
