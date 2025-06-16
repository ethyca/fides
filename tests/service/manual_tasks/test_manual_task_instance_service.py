from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Generator

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.attachment import Attachment, AttachmentReference
from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
from fides.api.models.manual_tasks.manual_task_instance import (
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus
from fides.api.schemas.manual_tasks.manual_task_status import (
    StatusTransitionNotAllowed,
    StatusType,
)
from fides.service.manual_tasks.manual_task_instance_service import (
    ManualTaskInstanceService,
)
from tests.service.manual_tasks.conftest import (
    ATTACHMENT_FIELD_KEY,
    CHECKBOX_FIELD_KEY,
    TEXT_FIELD_KEY,
)


@pytest.fixture
def manual_task_instance_service(db: Session) -> ManualTaskInstanceService:
    """Fixture for ManualTaskInstanceService."""
    return ManualTaskInstanceService(db)


@pytest.fixture
def manual_task_instance(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
) -> Generator[ManualTaskInstance, None, None]:
    """Fixture for a manual task instance."""
    service = ManualTaskInstanceService(db)
    instance = service.create_instance(
        task_id=manual_task.id,
        config_id=manual_task_config.id,
        entity_id="test_entity",
        entity_type="test_type",
    )
    yield instance
    instance.delete(db)


@pytest.fixture
def manual_task_submission_text(
    db: Session,
    manual_task_instance: ManualTaskInstance,
    manual_task_config_field_text: ManualTaskConfigField,
    respondent_user: FidesUser,
):
    """Fixture for a text field submission.

    Creates a submission with a text value for testing text field functionality.
    """
    submission = ManualTaskSubmission.create(
        db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "instance_id": manual_task_instance.id,
            "field_id": manual_task_config_field_text.id,
            "submitted_by": respondent_user.id,
            "data": {
                "field_key": TEXT_FIELD_KEY,
                "field_type": "text",
                "value": "test value",
            },
        },
    )
    yield submission
    submission.delete(db)


@pytest.fixture
def manual_task_submission_checkbox(
    db: Session,
    manual_task_instance: ManualTaskInstance,
    manual_task_config_field_checkbox: ManualTaskConfigField,
    respondent_user: FidesUser,
):
    """Fixture for a checkbox field submission.

    Creates a submission with a boolean value for testing checkbox field functionality.
    """
    submission = ManualTaskSubmission.create(
        db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "instance_id": manual_task_instance.id,
            "field_id": next(
                field
                for field in manual_task_instance.config.field_definitions
                if field.field_key == CHECKBOX_FIELD_KEY
            ).id,
            "submitted_by": respondent_user.id,
            "data": {
                "field_key": CHECKBOX_FIELD_KEY,
                "field_type": "checkbox",
                "value": True,
            },
        },
    )
    yield submission
    submission.delete(db)


@pytest.fixture
def manual_task_submission_attachment(
    db: Session,
    manual_task_instance: ManualTaskInstance,
    respondent_user: FidesUser,
):
    """Fixture for an attachment field submission.

    Creates a submission with an attachment value for testing file upload functionality.
    """
    submission = ManualTaskSubmission.create(
        db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "instance_id": manual_task_instance.id,
            "field_id": next(
                field
                for field in manual_task_instance.config.field_definitions
                if field.field_key == ATTACHMENT_FIELD_KEY
            ).id,
            "submitted_by": respondent_user.id,
            "data": {
                "field_key": ATTACHMENT_FIELD_KEY,
                "field_type": "attachment",
                "value": "test value",
            },
        },
    )
    yield submission
    submission.delete(db)


@pytest.fixture
def attachment(
    db: Session,
    manual_task_submission_attachment: ManualTaskSubmission,
    attachment_data: dict[str, Any],
):
    """Fixture for a file attachment.

    Creates a test file attachment and links it to a submission.
    """
    attachment = Attachment.create_and_upload(
        db=db,
        data=attachment_data,
        attachment_file=BytesIO(b"test contents"),
    )
    # Link attachment to submission
    AttachmentReference.create(
        db=db,
        data={
            "attachment_id": attachment.id,
            "reference_id": manual_task_submission_attachment.id,
            "reference_type": "manual_task_submission",
        },
    )
    yield attachment
    attachment.delete(db)


class TestInstanceCreationAndStatus:
    """Tests for instance creation and status management."""

    def test_create_instance(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
    ) -> None:
        """Test creating a new instance."""
        instance = manual_task_instance_service.create_instance(
            task_id=manual_task.id,
            config_id=manual_task_config.id,
            entity_id="test_entity",
            entity_type="test_type",
        )

        assert instance.task_id == manual_task.id
        assert instance.config_id == manual_task_config.id
        assert instance.entity_id == "test_entity"
        assert instance.entity_type == "test_type"
        assert instance.status == StatusType.pending

        # Verify log was created
        log = instance.logs[0]
        assert log.status == ManualTaskLogStatus.complete
        assert "Created task instance" in log.message

    def test_create_instance_error(
        self,
        manual_task_instance_service: ManualTaskInstanceService,
    ) -> None:
        """Test error handling in create_instance."""
        with pytest.raises(IntegrityError, match="violates foreign key constraint"):
            manual_task_instance_service.create_instance(
                task_id="invalid-task-id",
                config_id="invalid-config-id",
                entity_id="test_entity",
                entity_type="test_type",
            )

    def test_update_status(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
    ) -> None:
        """Test updating instance status."""
        manual_task_instance_service.update_status(
            instance_id=manual_task_instance.id,
            new_status=StatusType.in_progress,
            user_id="test_user",
        )

        assert manual_task_instance.status == StatusType.in_progress

        # Verify log was created
        log = manual_task_instance.logs[-1]
        assert log.status == ManualTaskLogStatus.complete
        assert "Updated task instance status" in log.message

    def test_update_status_invalid_transition(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
    ) -> None:
        """Test invalid status transition."""
        # Complete the instance
        with pytest.raises(StatusTransitionNotAllowed):
            manual_task_instance_service.complete_task_instance(
                task_id=manual_task_instance.task_id,
                config_id=manual_task_instance.config_id,
                instance_id=manual_task_instance.id,
                user_id="test_user",
            )

        manual_task_instance.status = StatusType.completed
        manual_task_instance.save(db)

        # Try to move back to in_progress
        with pytest.raises(StatusTransitionNotAllowed):
            manual_task_instance_service.update_status(
                instance_id=manual_task_instance.id,
                new_status=StatusType.in_progress,
                user_id="test_user",
            )

    def test_update_status_no_change(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
    ) -> None:
        """Test updating status to same value."""
        initial_log_count = len(manual_task_instance.logs)

        with pytest.raises(StatusTransitionNotAllowed):
            manual_task_instance_service.update_status(
                instance_id=manual_task_instance.id,
                new_status=StatusType.pending,  # Already pending
                user_id="test_user",
            )

        # Verify no new logs were created since status didn't change
        assert len(manual_task_instance.logs) == initial_log_count


class TestSubmissions:
    """Tests for submission creation and management."""

    def test_create_submission(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_text: ManualTaskConfigField,
    ) -> None:
        """Test creating a submission."""
        data = {
            "field_key": manual_task_config_field_text.field_key,
            "field_type": manual_task_config_field_text.field_type,
            "value": "test value",
        }

        submission = manual_task_instance_service.create_submission(
            instance_id=manual_task_instance.id,
            field_id=manual_task_config_field_text.id,
            data=data,
        )

        assert submission.instance_id == manual_task_instance.id
        assert submission.field_id == manual_task_config_field_text.id
        assert submission.data == data

        # Verify instance status was updated
        assert manual_task_instance.status == StatusType.in_progress

        # Verify logs were created - both submission creation and status update
        submission_log = next(
            log
            for log in manual_task_instance.logs
            if "Created task submission" in log.message
        )
        assert submission_log.status == ManualTaskLogStatus.complete

        status_log = next(
            log
            for log in manual_task_instance.logs
            if "Updated task instance status" in log.message
        )
        assert status_log.status == ManualTaskLogStatus.complete

    def test_update_submission(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_text: ManualTaskConfigField,
    ) -> None:
        """Test updating a submission."""
        # First create a submission
        initial_data = {
            "field_key": manual_task_config_field_text.field_key,
            "field_type": manual_task_config_field_text.field_type,
            "value": "initial value",
        }
        submission = manual_task_instance_service.create_submission(
            instance_id=manual_task_instance.id,
            field_id=manual_task_config_field_text.id,
            data=initial_data,
        )

        # Then update it
        updated_data = {
            "field_key": manual_task_config_field_text.field_key,
            "field_type": manual_task_config_field_text.field_type,
            "value": "updated value",
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "instance_id": manual_task_instance.id,
            "submitted_by": 1,
        }

        updated_submission = manual_task_instance_service.update_submission(
            instance_id=manual_task_instance.id,
            submission_id=submission.id,
            data=updated_data,
        )

        assert updated_submission.data == updated_data

        # Verify log was created
        log = manual_task_instance.logs[-1]
        assert log.status == ManualTaskLogStatus.complete
        assert "Updated task submission" in log.message

    def test_get_submission_for_field_not_found(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
    ) -> None:
        """Test getting submission for non-existent field."""
        submission = manual_task_instance_service.get_submission_for_field(
            instance_id=manual_task_instance.id,
            field_id="non-existent-field",
        )
        assert submission is None


class TestAttachments:
    """Tests for attachment management."""

    @pytest.mark.usefixtures("s3_client", "mock_s3_client")
    def test_delete_attachment_by_id_single_attachment(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_submission_attachment: ManualTaskSubmission,
        attachment: Attachment,
    ) -> None:
        """Test deleting the only attachment for a submission."""
        field = next(
            field
            for field in manual_task_instance.config.field_definitions
            if field.field_key == ATTACHMENT_FIELD_KEY
        )

        # Delete the attachment
        manual_task_instance_service.delete_attachment_by_id(
            submission_id=manual_task_submission_attachment.id,
            attachment_id=attachment.id,
        )

        # Verify submission was deleted
        assert (
            db.query(ManualTaskSubmission)
            .filter_by(id=manual_task_submission_attachment.id)
            .first()
            is None
        )

    @pytest.mark.usefixtures("mock_s3_client", "s3_client")
    def test_delete_attachment_by_id_multiple_attachments(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_submission_attachment: ManualTaskSubmission,
        respondent_user: FidesUser,
        attachment: Attachment,
        attachment_data: dict[str, Any],
    ) -> None:
        """Test deleting one of multiple attachments for a submission."""
        field = next(
            field
            for field in manual_task_instance.config.field_definitions
            if field.field_key == ATTACHMENT_FIELD_KEY
        )

        # Create second attachment
        attachment2 = Attachment.create_and_upload(
            db=db,
            data=attachment_data,
            attachment_file=BytesIO(b"test contents"),
        )
        AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment2.id,
                "reference_id": manual_task_submission_attachment.id,
                "reference_type": "manual_task_submission",
            },
        )

        # Delete one attachment
        manual_task_instance_service.delete_attachment_by_id(
            submission_id=manual_task_submission_attachment.id,
            attachment_id=attachment.id,
        )

        # Verify only one attachment was deleted
        assert db.query(Attachment).filter_by(id=attachment.id).first() is None
        assert db.query(Attachment).filter_by(id=attachment2.id).first() is not None
        assert (
            db.query(ManualTaskSubmission)
            .filter_by(id=manual_task_submission_attachment.id)
            .first()
            is not None
        )
        assert len(manual_task_submission_attachment.attachments) == 1
        assert manual_task_submission_attachment.attachments[0].id == attachment2.id

        attachment2.delete(db)

    @pytest.mark.usefixtures(
        "s3_client",
        "mock_s3_client",
        "manual_task_submission_checkbox",
        "manual_task_submission_text",
    )
    def test_delete_attachment_by_id_completed_instance(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_submission_attachment: ManualTaskSubmission,
        attachment: Attachment,
        respondent_user: FidesUser,
    ) -> None:
        """Test deleting attachment fails for completed instance."""
        field = next(
            field
            for field in manual_task_instance.config.field_definitions
            if field.field_key == ATTACHMENT_FIELD_KEY
        )

        # Complete the instance
        manual_task_instance_service.complete_task_instance(
            task_id=manual_task_instance.task_id,
            config_id=manual_task_instance.config_id,
            instance_id=manual_task_instance.id,
            user_id=respondent_user.id,
        )

        # Try to delete the attachment
        with pytest.raises(StatusTransitionNotAllowed, match="is already completed"):
            manual_task_instance_service.delete_attachment_by_id(
                submission_id=manual_task_submission_attachment.id,
                attachment_id=attachment.id,
            )

    @pytest.mark.usefixtures("s3_client", "mock_s3_client")
    def test_delete_attachment_missing_params(
        self,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_submission_attachment: ManualTaskSubmission,
    ) -> None:
        """Test delete_attachment_by_id with missing parameters."""
        with pytest.raises(ValueError, match="Submission with ID None does not exist"):
            manual_task_instance_service.delete_attachment_by_id(
                submission_id=None,
                attachment_id="some-attachment-id",
            )

        with pytest.raises(
            ValueError, match="Attachment with ID some-attachment-id not found"
        ):
            manual_task_instance_service.delete_attachment_by_id(
                submission_id=manual_task_submission_attachment.id,
                attachment_id="some-attachment-id",
            )


class TestTaskCompletion:
    """Tests for task completion functionality."""

    def test_complete_task_instance(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_text: ManualTaskConfigField,
        respondent_user: FidesUser,
    ) -> None:
        """Test completing a task instance."""
        # Submit all required fields
        for field in manual_task_instance.config.field_definitions:
            if field.field_metadata.get("required"):
                data = {
                    "field_key": field.field_key,
                    "field_type": field.field_type,
                    "value": "test value" if field.field_type != "checkbox" else True,
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "instance_id": manual_task_instance.id,
                    "submitted_by": respondent_user.id,
                }
                manual_task_instance_service.create_submission(
                    instance_id=manual_task_instance.id,
                    field_id=field.id,
                    data=data,
                )

        # Now complete the instance
        manual_task_instance_service.complete_task_instance(
            task_id=manual_task_instance.task_id,
            config_id=manual_task_instance.config_id,
            instance_id=manual_task_instance.id,
            user_id="test_user",
        )

        assert manual_task_instance.status == StatusType.completed
        assert manual_task_instance.completed_by_id == "test_user"
        assert manual_task_instance.completed_at is not None

        # Verify log was created
        completed_log = next(
            log
            for log in manual_task_instance.logs
            if "Completed task instance" in log.message
        )
        assert completed_log.status == ManualTaskLogStatus.complete
        assert completed_log.details.get("completed_by") == "test_user"

    def test_validate_instance_for_submission_completed(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        respondent_user: FidesUser,
    ) -> None:
        """Test validation fails for completed instance."""
        # Submit all required fields
        for field in manual_task_instance.config.field_definitions:
            if field.field_metadata.get("required"):
                data = {
                    "field_key": field.field_key,
                    "field_type": field.field_type,
                    "value": "test value" if field.field_type != "checkbox" else True,
                    "task_id": manual_task_instance.task_id,
                    "config_id": manual_task_instance.config_id,
                    "instance_id": manual_task_instance.id,
                    "submitted_by": respondent_user.id,
                }
                manual_task_instance_service.create_submission(
                    instance_id=manual_task_instance.id,
                    field_id=field.id,
                    data=data,
                )

        manual_task_instance_service.complete_task_instance(
            task_id=manual_task_instance.task_id,
            config_id=manual_task_instance.config_id,
            instance_id=manual_task_instance.id,
            user_id="test_user",
        )

        with pytest.raises(StatusTransitionNotAllowed, match="is already completed"):
            manual_task_instance_service._validate_instance_for_submission(
                manual_task_instance.id
            )
