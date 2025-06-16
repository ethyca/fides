from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.attachment import Attachment
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfigField
from fides.api.models.manual_tasks.manual_task_instance import (
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.schemas.manual_tasks.manual_task_status import (
    StatusTransitionNotAllowed,
    StatusType,
)
from fides.service.manual_tasks.utils import validate_fields, with_task_logging


class ManualTaskInstanceService:
    def __init__(self, db: Session):
        self.db = db

    # ------- Private Helper Methods -------
    def _validate_instance_for_submission(self, instance_id: str) -> ManualTaskInstance:
        """Validate that an instance exists and can accept changes.

        This validation is specifically for operations that modify an instance
        (like submissions, status changes, etc). For task or config level operations,
        instance validation is not needed.

        Args:
            instance_id: ID of the instance to validate

        Returns:
            ManualTaskInstance: The validated instance

        Raises:
            ValueError: If instance not found
            StatusTransitionNotAllowed: If instance is completed
        """
        instance = self.db.query(ManualTaskInstance).filter_by(id=instance_id).first()
        if not instance:
            raise ValueError(f"Instance with ID {instance_id} not found")

        # Validate that we can transition from completed (will raise if completed)
        if instance.status == StatusType.completed:
            raise StatusTransitionNotAllowed(
                "Instance is already completed, no further changes allowed"
            )

        return instance

    def _validate_field_for_submission(
        self, field_id: str, data: dict[str, Any]
    ) -> ManualTaskConfigField:
        """Validate the field for a submission.

        Args:
            field_id: ID of the field to validate
            data: Field data to validate

        Returns:
            ManualTaskConfigField: The validated field

        Raises:
            ValueError: If the field is not found or data is invalid
        """
        field = ManualTaskConfigField.get_by_key_or_id(
            db=self.db, data={"id": field_id}
        )
        if not field:
            raise ValueError(f"Field with ID {field_id} not found")

        # Validate submission data against field definition
        validate_fields([data], is_submission=True)
        return field

    # ------- Public Instance Methods -------

    @with_task_logging("Created task instance")
    def create_instance(
        self, task_id: str, config_id: str, entity_id: str, entity_type: str
    ) -> tuple[ManualTaskInstance, dict[str, Any]]:
        """Create a new instance for an entity.

        Returns:
            tuple(ManualTaskInstance, log_details) The log_details are intercepted by the
            `with_task_logging` decorator. The instance is returned to allow for chaining.
        """
        instance = ManualTaskInstance.create(
            self.db,
            data={
                "task_id": task_id,
                "config_id": config_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
            },
        )
        return instance, {
            "task_id": task_id,
            "config_id": config_id,
            "instance_id": instance.id,
            "details": {
                "entity_type": entity_type,
            },
        }

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

    @with_task_logging("Updated task instance status")
    def update_status(
        self,
        instance_id: str,
        new_status: Optional[StatusType] = None,
        user_id: Optional[str] = None,
    ) -> tuple[ManualTaskInstance, dict[str, Any]]:
        """Update instance status with logging.

        Args:
            instance_id: The instance ID
            new_status: Optional new status
            user_id: Optional user ID making the change

        Returns:
            tuple(ManualTaskInstace, log_details) The log_details are intercepted by the
            `with_task_logging` decorator. The instance is returned to allow for chaining.
        """
        instance = self._validate_instance_for_submission(instance_id)
        has_submissions = len(instance.submissions) > 0

        # If no new status is provided, use target status
        if not new_status:
            new_status = (
                StatusType.in_progress if has_submissions else StatusType.pending
            )

        previous_status = instance.status
        instance.update_status(self.db, new_status, user_id)
        return instance, {
            "instance_id": instance.id,
            "task_id": instance.task_id,
            "config_id": instance.config_id,
            "details": {
                "previous_status": previous_status,
                "new_status": new_status,
                "user_id": user_id,
            },
        }

    @with_task_logging("Created task submission")
    def create_submission(
        self,
        instance_id: str,
        field_id: str,
        data: dict[str, Any],
    ) -> tuple[ManualTaskSubmission, dict[str, Any]]:
        """Create a new submission for a field.

        Returns:
            tuple(ManualTaskSubmission, log_details) The log_details are intercepted by the
            `with_task_logging` decorator. The submission is returned to allow for chaining.
        """
        instance = self._validate_instance_for_submission(instance_id)
        field = self._validate_field_for_submission(field_id, data)
        # if there is a submission for this field, raise an error
        if instance.get_submission_for_field(field_id):
            raise ValueError(
                f"Submission for field {field.field_key} already exists for instance {instance.id}"
            )

        submission_data = {
            "task_id": instance.task_id,
            "config_id": instance.config_id,
            "instance_id": instance.id,
            "field_id": field.id,
            "data": data,
        }
        submission = ManualTaskSubmission.create(
            self.db,
            data=submission_data,
        )
        # Update instance status
        try:
            self.update_status(instance.id)
        except StatusTransitionNotAllowed as e:
            logger.info(f"Status not transitioning: {e}")

        # Return submission and logging details
        log_data = {
            "task_id": instance.task_id,
            "config_id": instance.config_id,
            "instance_id": instance.id,
            "details": {
                "field_key": field.field_key,
                "field_type": field.field_type,
            },
        }
        return submission, log_data

    @with_task_logging("Updated task submission")
    def update_submission(
        self,
        instance_id: str,
        submission_id: str,
        data: dict[str, Any],
    ) -> tuple[ManualTaskSubmission, dict[str, Any]]:
        """Update a submission for a field."""
        instance = self._validate_instance_for_submission(instance_id)
        # if this submission does not exist on this instance, raise an error
        submission = [
            submission
            for submission in instance.submissions
            if submission.id == submission_id
        ][0]
        if not submission:
            raise ValueError(
                f"Submission with ID {submission_id} does not exist on instance {instance.id}"
            )
        if not submission.field_id:
            raise ValueError(
                f"Submission with ID {submission_id} does not have a field_id"
            )
        self._validate_field_for_submission(submission.field_id, data)

        # Update the submission
        submission.update(
            self.db,
            data={
                "data": data,
            },
        )
        try:
            self.update_status(instance.id)
        except StatusTransitionNotAllowed as e:
            logger.info(f"Status not transitioning: {e}")

        return submission, {
            "task_id": instance.task_id,
            "config_id": instance.config_id,
            "instance_id": instance.id,
            "details": {
                "field_key": submission.field.field_key,
                "field_type": submission.field.field_type,
            },
        }

    @with_task_logging("Delete task attachment")
    def delete_attachment_by_id(
        self,
        submission_id: str,
        attachment_id: str,
    ) -> None:
        """Delete an attachment for a field.

        Args:
            submission_id: ID of the submission containing the attachment
            attachment_id: ID of the attachment to delete

        Raises:
            ValueError: If submission or attachment not found
            StatusTransitionNotAllowed: If instance is completed
        """
        # Get the submission
        submission = (
            self.db.query(ManualTaskSubmission).filter_by(id=submission_id).first()
        )
        if not submission:
            raise ValueError(f"Submission with ID {submission_id} does not exist")

        # Check if instance is completed
        if submission.instance.status == StatusType.completed:
            raise StatusTransitionNotAllowed(
                "Instance is already completed, no further changes allowed"
            )

        # Get the attachment
        attachment = self.db.query(Attachment).filter_by(id=attachment_id).first()
        if not attachment:
            raise ValueError(f"Attachment with ID {attachment_id} not found")

        if attachment not in submission.attachments:
            raise ValueError(
                f"Attachment with ID {attachment_id} does not exist on submission {submission.id}"
            )

        # if there is only one attachment and the submission is for an attachment field, delete the submission
        if (
            len(submission.attachments) == 1
            and submission.field.field_type == "attachment"
        ):
            attachment.delete(self.db)
            logger.info(
                f"Deleting submission {submission.id} for {submission.field.field_key}"
            )
            submission.delete(self.db)
        else:
            logger.info(
                f"Deleting attachment {attachment.id} for submission {submission.id}"
            )
            attachment.delete(self.db)

    @with_task_logging("Completed task instance")
    def complete_task_instance(
        self, task_id: str, config_id: str, instance_id: str, user_id: str
    ) -> tuple[ManualTaskInstance, dict[str, Any]]:
        """Complete a task instance. This will not happen automatically. It must be called with a user_id.

        Args:
            task_id: The task ID
            config_id: The config ID
            instance_id: The instance ID to complete
            user_id: The user ID completing the instance

        Returns:
            ManualTaskInstance: The completed instance
        """
        instance = self._validate_instance_for_submission(instance_id)

        # Check that all required fields have submissions
        missing_required_fields = [
            field.field_key
            for field in instance.required_fields
            if not instance.get_submission_for_field(field.id)
        ]
        if len(missing_required_fields) > 0:
            raise StatusTransitionNotAllowed(
                f"Cannot complete task instance. Missing required fields: {', '.join(missing_required_fields)}"
            )

        # Update status to completed
        instance.update_status(self.db, StatusType.completed, user_id)
        instance.completed_by_id = user_id
        instance.save(self.db)

        # Return both instance and details for proper logging
        return instance, {
            "task_id": task_id,
            "config_id": config_id,
            "instance_id": instance_id,
            "details": {"completed_by": user_id},
        }
