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

    def _create_log_data(
        self,
        task_id: str,
        config_id: str,
        instance_id: str,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        """Create standard log data structure."""
        return {
            "task_id": task_id,
            "config_id": config_id,
            "instance_id": instance_id,
            "details": details,
        }

    def _get_instance(
        self, instance_id: str, allow_completed: bool = False
    ) -> ManualTaskInstance:
        """Get and validate instance."""
        instance = self.db.query(ManualTaskInstance).filter_by(id=instance_id).first()
        if not instance:
            raise ValueError(f"Instance with ID {instance_id} not found")

        if not allow_completed and instance.status == StatusType.completed:
            raise StatusTransitionNotAllowed(
                "Instance is already completed, no further changes allowed"
            )

        return instance

    def _get_field(
        self, field_id: str, validate_data: Optional[dict[str, Any]] = None
    ) -> ManualTaskConfigField:
        """Get and validate field."""
        field = ManualTaskConfigField.get_by_key_or_id(
            db=self.db, data={"id": field_id}
        )
        if not field:
            raise ValueError(f"Field with ID {field_id} not found")

        if validate_data:
            validate_fields([validate_data], is_submission=True)

        return field

    def _update_instance_status(
        self,
        instance: ManualTaskInstance,
        new_status: Optional[StatusType] = None,
        user_id: Optional[str] = None,
        silent: bool = False,
    ) -> None:
        """Update instance status with optional error suppression."""
        try:
            if not new_status:
                new_status = (
                    StatusType.in_progress
                    if instance.submissions
                    else StatusType.pending
                )
            instance.update_status(self.db, new_status, user_id)
        except StatusTransitionNotAllowed as e:
            if not silent:
                raise
            logger.info(f"Status not transitioning: {e}")

    @with_task_logging("Created task instance")
    def create_instance(
        self, task_id: str, config_id: str, entity_id: str, entity_type: str
    ) -> tuple[ManualTaskInstance, dict[str, Any]]:
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
        return instance, self._create_log_data(
            task_id, config_id, instance.id, {"entity_type": entity_type}
        )

    def get_submission_for_field(
        self, instance_id: str, field_id: str
    ) -> Optional[ManualTaskSubmission]:
        """Get the submission for a specific field."""
        return self._get_instance(instance_id).get_submission_for_field(field_id)

    @with_task_logging("Updated task instance status")
    def update_status(
        self,
        instance_id: str,
        new_status: Optional[StatusType] = None,
        user_id: Optional[str] = None,
    ) -> tuple[ManualTaskInstance, dict[str, Any]]:
        """Update instance status with logging."""
        instance = self._get_instance(instance_id)
        previous_status = instance.status
        self._update_instance_status(instance, new_status, user_id)

        return instance, self._create_log_data(
            instance.task_id,
            instance.config_id,
            instance.id,
            {
                "previous_status": previous_status,
                "new_status": instance.status,
                "user_id": user_id,
            },
        )

    @with_task_logging("Created task submission")
    def create_submission(
        self,
        instance_id: str,
        field_id: str,
        data: dict[str, Any],
    ) -> tuple[ManualTaskSubmission, dict[str, Any]]:
        """Create a new submission for a field."""
        instance = self._get_instance(instance_id)
        field = self._get_field(field_id, data)

        if instance.get_submission_for_field(field_id):
            raise ValueError(
                f"Submission for field {field.field_key} already exists for instance {instance.id}"
            )

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

        # Update instance status to in_progress
        self._update_instance_status(instance, StatusType.in_progress, silent=True)

        return submission, self._create_log_data(
            instance.task_id,
            instance.config_id,
            instance.id,
            {
                "field_key": field.field_key,
                "field_type": field.field_type,
            },
        )

    @with_task_logging("Updated task submission")
    def update_submission(
        self,
        instance_id: str,
        submission_id: str,
        data: dict[str, Any],
    ) -> tuple[ManualTaskSubmission, dict[str, Any]]:
        """Update a submission for a field."""
        instance = self._get_instance(instance_id)
        submission = next(
            (s for s in instance.submissions if s.id == submission_id),
            None,
        )
        if not submission or not submission.field_id:
            raise ValueError(f"Valid submission with ID {submission_id} not found")

        field = self._get_field(submission.field_id, data)
        submission.update(self.db, data={"data": data})
        self._update_instance_status(instance, silent=True)

        return submission, self._create_log_data(
            instance.task_id,
            instance.config_id,
            instance.id,
            {
                "field_key": field.field_key,
                "field_type": field.field_type,
            },
        )

    @with_task_logging("Delete task attachment")
    def delete_attachment_by_id(
        self,
        submission_id: str,
        attachment_id: str,
    ) -> None:
        """Delete an attachment for a field."""
        submission = (
            self.db.query(ManualTaskSubmission).filter_by(id=submission_id).first()
        )
        if not submission:
            raise ValueError(f"Submission with ID {submission_id} does not exist")

        self._get_instance(
            submission.instance_id
        )  # Validates instance is not completed

        attachment = self.db.query(Attachment).filter_by(id=attachment_id).first()
        if not attachment or attachment not in submission.attachments:
            raise ValueError(
                f"Attachment {attachment_id} not found in submission {submission_id}"
            )

        # Delete attachment and optionally submission
        attachment.delete(self.db)
        if (
            len(submission.attachments) == 1
            and submission.field.field_type == "attachment"
        ):
            submission.delete(self.db)

    @with_task_logging("Completed task instance")
    def complete_task_instance(
        self, task_id: str, config_id: str, instance_id: str, user_id: str
    ) -> tuple[ManualTaskInstance, dict[str, Any]]:
        """Complete a task instance."""
        instance = self._get_instance(instance_id)

        missing_fields = [
            field.field_key
            for field in instance.required_fields
            if not instance.get_submission_for_field(field.id)
        ]
        if missing_fields:
            raise StatusTransitionNotAllowed(
                f"Cannot complete task instance. Missing required fields: {', '.join(missing_fields)}"
            )

        instance.update_status(self.db, StatusType.completed, user_id)
        instance.completed_by_id = user_id
        instance.save(self.db)

        return instance, self._create_log_data(
            task_id, config_id, instance_id, {"completed_by": user_id}
        )
