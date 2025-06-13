from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.attachment import Attachment
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfigField
from fides.api.models.manual_tasks.manual_task_instance import (
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus
from fides.api.schemas.manual_tasks.manual_task_status import (
    StatusTransitionNotAllowed,
    StatusType,
)
from fides.service.manual_tasks.utils import validate_fields, with_error_logging


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
            raise StatusTransitionNotAllowed(
                f"Instance with ID {instance.id} is already completed"
            )

        return instance

    def _validate_field_for_submission(
        self, field_id: str, data: dict[str, Any]
    ) -> ManualTaskConfigField:
        """Validate the field for a submission."""
        field = ManualTaskConfigField.get_by_key_or_id(
            db=self.db, data={"id": field_id}
        )
        if not field:
            raise ValueError(f"Field with ID {field_id} not found")
        if field.field_key != data.get("field_key"):
            raise ValueError(
                "Data must be for field. Provided field id does not match field key."
            )
        if field.field_type != data.get("field_type"):
            raise ValueError(
                "Data must be for field. Provided field type does not match field type."
            )
        return field

    # ------- Public Instance Methods -------

    @with_error_logging("Create task instance")
    def create_instance(
        self, task_id: str, config_id: str, entity_id: str, entity_type: str
    ) -> ManualTaskInstance:
        """Create a new instance for an entity."""
        instance = ManualTaskInstance.create(
            self.db,
            data={
                "task_id": task_id,
                "config_id": config_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
            },
        )
        return instance

    def get_submission_for_field(
        self, instance_id: str, field_id: str
    ) -> Optional["ManualTaskSubmission"]:
        """Get the submission for a specific field.
        Args:
            field_id: ID of the field to get submission for
        Returns:
            Optional[ManualTaskSubmission]: The submission if it exists
        """
        instance = self._validate_instance_for_submission(instance_id)
        return instance.get_submission_for_field(field_id)

    @with_error_logging("Update task instance status")
    def update_status(
        self,
        db: Session,
        instance_id: str,
        new_status: StatusType,
        user_id: Optional[str] = None,
    ) -> ManualTaskInstance:
        """Update instance status with logging.

        Args:
            db: Database session
            instance_id: The instance ID
            new_status: The new status
            user_id: Optional user ID making the change

        Returns:
            ManualTaskInstance: The updated instance
        """
        instance = self._validate_instance_for_submission(instance_id)
        previous_status = instance.status
        instance.update_status(db, new_status, user_id)
        return instance

    @with_error_logging("Update task instance status from submissions")
    def update_status_from_submissions(
        self, db: Session, instance_id: str
    ) -> ManualTaskInstance:
        """Update the instance status based on submissions.
        The status updates when a new submissions is created or updated. This function can
        transition to in_progress or pending.
        Only a user can transition to completed.

        Args:
            db: Database session
            instance_id: The instance ID to update

        Returns:
            ManualTaskInstance: The updated instance
        """
        instance = self._validate_instance_for_submission(instance_id)
        if instance.status == StatusType.completed:
            return instance
        if not instance.submissions:
            return instance

        # Check if any fields have submissions
        any_submissions = len(instance.submissions) > 0

        # Update status based on field submissions
        if instance.status == StatusType.pending and any_submissions:
            # First transition to in_progress if we have any submissions
            self.update_status(db, instance_id, StatusType.in_progress)
        if not any_submissions and instance.status != StatusType.pending:
            # Only go back to pending if we have no valid submissions
            self.update_status(db, instance_id, StatusType.pending)

        return instance

    @with_error_logging("Create or update task submission")
    def create_or_update_submission(
        self, instance_id: str, field_id: str, data: dict[str, Any]
    ) -> ManualTaskSubmission:
        """Create or update a submission for a field."""
        instance = self._validate_instance_for_submission(instance_id)
        field = self._validate_field_for_submission(field_id, data)
        # Validate data against field metadata
        validate_fields([data])

        submission = self.get_submission_for_field(instance_id, field_id)
        # If the submission does not exist, create it
        if submission is None:
            logger.info(f"Creating submission for field {field.field_key}")
            return self.create_submission(instance, field, data)

        # If the submission exists, update it
        logger.info(f"Updating submission for field {field.field_key}")
        return self.update_submission(instance, submission, data)

    @with_error_logging("Create task submission")
    def create_submission(
        self,
        instance: ManualTaskInstance,
        field: ManualTaskConfigField,
        data: dict[str, Any],
    ) -> ManualTaskSubmission:
        """Create a new submission for a field."""
        submission = ManualTaskSubmission.create(
            self.db,
            data={
                "task_id": instance.task_id,
                "config_id": instance.config_id,
                "instance_id": instance.id,
                "field_id": field.id,
                "data": data,
            },
        )
        # Update instance status
        self.update_status_from_submissions(self.db, instance.id)
        return submission

    @with_error_logging("Update task submission")
    def update_submission(
        self,
        instance: ManualTaskInstance,
        submission: ManualTaskSubmission,
        data: dict[str, Any],
    ) -> ManualTaskSubmission:
        """Update a submission for a field."""
        submission.update(
            self.db,
            data={
                "data": data,
            },
        )
        self.update_status_from_submissions(self.db, instance.id)
        return submission

    @with_error_logging("Delete task attachment")
    def delete_attachment_by_id(
        self,
        instance_id: Optional[str],
        field_id: Optional[str],
        submission_id: Optional[str],
        attachment_id: str,
    ) -> None:
        """Delete an attachment for a field."""
        # Get the attachment
        attachment = self.db.query(Attachment).filter_by(id=attachment_id).first()
        if not attachment:
            raise ValueError(f"Attachment with ID {attachment_id} not found")

        # Get the submission
        submission = None
        if submission_id:
            submission = ManualTaskSubmission.get_by_id(
                db=self.db, data={"id": submission_id}
            )
        elif instance_id and field_id:
            submission = self.get_submission_for_field(instance_id, field_id)

        if not submission:
            raise ValueError(
                f"Attachment with ID {attachment_id} not found for submission with ID {submission.id}"
            )

        # if there is only one attachment and the submission is for an attachment field, delete the submission
        if len(submission.attachments) == 1 and submission.field.field_type == "attachment":
            attachment.delete(self.db)
            logger.info(
                f"Deleting submission {submission.id} for field {submission.field.field_key}"
            )
            submission.delete(self.db)
        else:
            logger.info(
                f"Deleting attachment {attachment.id} for submission {submission.id}"
            )
            attachment.delete(self.db)

        if instance_id:
            self.update_status_from_submissions(self.db, instance_id)

    @with_error_logging("Complete task instance")
    def complete_task_instance(self, instance_id: str, user_id: str) -> ManualTaskInstance:
        """Complete a task instance.

        Args:
            instance_id: The instance ID to complete
            user_id: The user ID completing the instance

        Returns:
            ManualTaskInstance: The completed instance
        """
        instance = self._validate_instance_for_submission(instance_id)

        # Check that all required fields have submissions
        missing_required_fields = []
        for field in instance.config.field_definitions:
            if field.field_metadata.get("required"):
                submission = instance.get_submission_for_field(field.id)
                if not submission:
                    missing_required_fields.append(field.field_key)

        if missing_required_fields:
            raise ValueError(
                f"Cannot complete task instance. Missing required fields: {', '.join(missing_required_fields)}"
            )

        # Update status to completed
        instance.update_status(self.db, StatusType.completed, user_id)
        instance.completed_by_id = user_id
        instance.save(self.db)

        return instance
