from typing import Any, Optional

from loguru import logger
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
from fides.api.models.manual_tasks.manual_task_instance import ManualTaskInstance, ManualTaskSubmission
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskAttachmentField,
    ManualTaskCheckboxField,
    ManualTaskConfigResponse,
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskTextField,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus, StatusType
from fides.service.manual_tasks.utils import validate_fields


class ManualTaskInstanceService:
    def __init__(self, db: Session):
        self.db = db

    # ------- Private Helper Methods -------
    def _validate_instance_for_submission(self, instance_id: str) -> ManualTaskInstance:
        """Validate the instance and field for a submission."""

        instance = self.db.query(ManualTaskInstance).filter_by(id=instance_id).first()
        if not instance:
            raise ValueError(f"Instance with ID {instance_id} not found")
        if instance.status == StatusType.completed:
            raise ValueError(f"Instance with ID {instance.id} is already completed")

        return instance

    def _validate_field_for_submission(self, field_id: str, data: dict[str, Any]) -> ManualTaskConfigField:
        """Validate the field for a submission."""
        field = ManualTaskConfigField.get_by_key_or_id(
            db=self.db, data={"id": field_id}
        )
        if not field:
            raise ValueError(f"Field with ID {field_id} not found")
        if field.field_key != data.get("field_key"):
            raise ValueError(f"Data must be for field. Provided field id does not match field key.")
        if field.field_type != data.get("field_type"):
            raise ValueError(f"Data must be for field. Provided field type does not match field type.")

    # ------- Public Instance Methods -------

    def create_instance(self, task_id: str, config_id: str, entity_id: str, entity_type: str) -> ManualTaskInstance:
        """Create a new instance for an entity."""
        try:
            instance = ManualTaskInstance.create(
                self.db,
                data = {
                    "task_id": task_id,
                    "config_id": config_id,
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                }
            )
            # Log instance creation (instance-level log)
            ManualTaskLog.create_log(
                db=self.db,
                task_id=task_id,
                config_id=config_id,
                instance_id=instance.id,
                status=ManualTaskLogStatus.complete,
                message=f"Created task instance for {entity_type} {entity_id}",
                details={
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "initial_status": StatusType.pending,
                },
            )
            return instance
        except Exception as e:
            ManualTaskLog.create_log(
                db=self.db,
                task_id=task_id,
                config_id=config_id,
                instance_id=instance.id,
                status=ManualTaskLogStatus.error,
                message=f"Error creating task instance for {entity_type} {entity_id}",
                details={
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "error": str(e),
                },
            )
            raise

    def get_submission_for_field(
        self, instance_id: str, field_id: str
    ) -> Optional["ManualTaskSubmission"]:
        """Get the submission for a specific field.
        Args:
            field_id: ID of the field to get submission for
        Returns:
            Optional[ManualTaskSubmission]: The submission if it exists
        """
        instance = self.db.query(ManualTaskInstance).filter_by(id=instance_id).first()
        return next((s for s in instance.submissions if s.field_id == field_id), None)

    def update_status(
        self, db: Session, instance_id: str, new_status: StatusType, user_id: Optional[str] = None
    ) -> None:
        """Override update_status to add logging."""
        instance = self.db.query(ManualTaskInstance).filter_by(id=instance_id).first()
        previous_status = instance.status
        instance.update_status(db, new_status, user_id)

        # Only create a log if the status actually changed
        if previous_status != new_status:
            # Create a log entry for the status transition
            ManualTaskLog.create_log(
                db=db,
                task_id=instance.task_id,
                config_id=instance.config_id,
                instance_id=instance.id,
                status=ManualTaskLogStatus.in_processing,
                message=f"Task instance status transitioning from {previous_status} to {new_status}",
                details={
                    "previous_status": previous_status,
                    "new_status": new_status,
                    "user_id": user_id,
                },
            )

    def update_status_from_submissions(self, db: Session, instance_id: str) -> None:
        """Update the instance status based on submissions.
        The status updates when a new submissions is created or updated. This function can
        transition to in_progress or pending.
        Only a user can transition to completed.
        Args:
            db: Database session
        """
        instance = self.db.query(ManualTaskInstance).filter_by(id=instance_id).first()
        if instance.status == StatusType.completed:
            return
        if not instance.submissions:
            return

        # Check if any fields have submissions
        any_submissions = len(instance.submissions) > 0

        # Update status based on field submissions
        if instance.status == StatusType.pending and any_submissions:
            # First transition to in_progress if we have any submissions
            self.update_status(db, instance_id, StatusType.in_progress)
        if not any_submissions and instance.status != StatusType.pending:
            # Only go back to pending if we have no valid submissions
            self.update_status(db, instance_id, StatusType.pending)

    def create_submission(
            self,
            instance: ManualTaskInstance,
            field: ManualTaskConfigField,
            data: dict[str, Any]
        ) -> ManualTaskSubmission:
        """Create a new submission for a field."""
        try:
            submission = ManualTaskSubmission.create(
                self.db,
                data = {
                    "instance_id": instance.id,
                    "field_id": field.id,
                    "data": data,
                }
            )
            # Log submission creation
            ManualTaskLog.create_log(
                db=self.db,
                task_id=instance.task_id,
                config_id=instance.config_id,
                instance_id=instance.id,
                status=ManualTaskLogStatus.complete,
                message=f"Created submission for field {field.field_key}",
            )
            # Update instance status
            self.update_status_from_submissions(self.db, instance.id)
            return submission
        except Exception as e:
            ManualTaskLog.create_log(
                db=self.db,
                task_id=instance.task_id,
                config_id=instance.config_id,
                instance_id=instance.id,
                status=ManualTaskLogStatus.error,
                message=f"Error creating submission for field {field.field_key}",
                details={
                    "error": str(e),
                    "field_key": field.field_key,
                    "field_type": field.field_type,
                },
            )
            raise

    def update_submission(
        self, instance: ManualTaskInstance, submission: ManualTaskSubmission, data: dict[str, Any]
    ) -> ManualTaskSubmission:
        """Update a submission for a field."""
        try:
            submission.update(
                self.db,
                data = {
                    "data": data,
                }
            )
            ManualTaskLog.create_log(
                db=self.db,
                task_id=data["task_id"],
                config_id=data["config_id"],
                instance_id=data["instance_id"],
                status=ManualTaskLogStatus.complete,
                message=f"Updated submission for field {submission.field.field_key}",
                details={
                    "field_key": submission.field.field_key,
                    "field_type": submission.field.field_type,
                    "submitted_by": data["submitted_by"],
                    "status": instance.status,
                },
            )
            self.update_status_from_submissions(self.db, instance.id)
            return submission
        except Exception as e:
            ManualTaskLog.create_log(
                db=self.db,
                task_id=instance.task_id,
                config_id=instance.config_id,
                instance_id=instance.id,
                status=ManualTaskLogStatus.error,
                message=f"Error updating submission for field {submission.field.field_key}",
                details={
                    "error": str(e),
                    "field_key": submission.field.field_key,
                    "field_type": submission.field.field_type,
                },
            )
            raise

    def create_or_update_submission(self, instance_id: str, field_id: str, data: dict[str, Any]) -> ManualTaskSubmission:
        """Create or update a submission for a field."""
        instance = self._validate_instance_for_submission(instance_id)
        field = self._validate_field_for_submission(field_id, data)
        # Validate data against field metadata
        validate_fields([data])

        if self.get_submission_for_field(instance_id, field_id) == None:
            return self.create_submission(instance, field, data)
        else:
            return self.update_submission(instance, field, data)
