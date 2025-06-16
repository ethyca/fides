from io import BytesIO
from typing import Any, Generator

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.attachment import Attachment, AttachmentReference
from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.manual_tasks.manual_task_instance import (
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.schemas.manual_tasks.manual_task_status import (
    StatusTransitionNotAllowed,
    StatusType,
)
from fides.service.manual_tasks.manual_task_instance_service import (
    ManualTaskInstanceService,
)


@pytest.fixture
def manual_task_instance_service(db: Session) -> ManualTaskInstanceService:
    """Fixture for ManualTaskInstanceService."""
    return ManualTaskInstanceService(db)


@pytest.fixture
def manual_task_instance(
    db: Session, manual_task: ManualTask, manual_task_config: ManualTaskConfig
) -> Generator[ManualTaskInstance, None, None]:
    """Fixture for a manual task instance."""
    instance = ManualTaskInstanceService(db).create_instance(
        task_id=manual_task.id,
        config_id=manual_task_config.id,
        entity_id="test_entity",
        entity_type="test_type",
    )
    yield instance
    instance.delete(db)


@pytest.fixture
def submission_data(
    manual_task_instance: ManualTaskInstance,
    respondent_user: FidesUser,
    field_type: str = "text",
) -> dict[str, Any]:
    """Base submission data fixture."""
    field = next(
        f
        for f in manual_task_instance.config.field_definitions
        if f.field_type == field_type
    )
    return {
        "task_id": manual_task_instance.task_id,
        "config_id": manual_task_instance.config_id,
        "instance_id": manual_task_instance.id,
        "field_id": field.id,
        "submitted_by": respondent_user.id,
        "data": {
            "field_key": field.field_key,
            "field_type": field_type,
            "value": "test value" if field_type != "checkbox" else True,
        },
    }


@pytest.fixture
def manual_task_submission(
    db: Session, submission_data: dict[str, Any]
) -> Generator[ManualTaskSubmission, None, None]:
    """Generic submission fixture."""
    submission = ManualTaskSubmission.create(db, data=submission_data)
    yield submission
    submission.delete(db)


@pytest.fixture
def attachment_field_submission_data(
    manual_task_instance: ManualTaskInstance,
    respondent_user: FidesUser,
) -> dict[str, Any]:
    """Fixture for submission data with attachment field type."""
    field = next(
        f
        for f in manual_task_instance.config.field_definitions
        if f.field_type == "attachment"
    )
    return {
        "task_id": manual_task_instance.task_id,
        "config_id": manual_task_instance.config_id,
        "instance_id": manual_task_instance.id,
        "field_id": field.id,
        "submitted_by": respondent_user.id,
        "data": {
            "field_key": field.field_key,
            "field_type": "attachment",
            "value": None,
        },
    }


@pytest.fixture
def attachment_field_submission(
    db: Session, attachment_field_submission_data: dict[str, Any]
) -> Generator[ManualTaskSubmission, None, None]:
    """Fixture for a submission with attachment field type."""
    submission = ManualTaskSubmission.create(db, data=attachment_field_submission_data)
    yield submission
    submission.delete(db)


class TestInstanceOperations:
    """Tests for instance operations."""

    def test_create_instance(
        self,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
    ) -> None:
        """Test instance creation and validation."""
        instance = manual_task_instance_service.create_instance(
            task_id=manual_task.id,
            config_id=manual_task_config.id,
            entity_id="test_entity",
            entity_type="test_type",
        )

        assert instance.task_id == manual_task.id
        assert instance.config_id == manual_task_config.id
        assert instance.status == StatusType.pending
        assert "Created task instance" in instance.logs[0].message

        # Test error cases
        with pytest.raises(IntegrityError):
            manual_task_instance_service.create_instance(
                task_id="invalid-id",
                config_id="invalid-id",
                entity_id="test",
                entity_type="test",
            )

    def test_instance_status_transitions(
        self,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
    ) -> None:
        """Test instance status updates and validations."""
        # Test valid transition
        manual_task_instance_service.update_status(
            instance_id=manual_task_instance.id,
            new_status=StatusType.in_progress,
        )
        assert manual_task_instance.status == StatusType.in_progress

        # Test invalid transitions
        manual_task_instance.status = StatusType.completed
        manual_task_instance.save(manual_task_instance_service.db)

        with pytest.raises(StatusTransitionNotAllowed):
            manual_task_instance_service.update_status(
                instance_id=manual_task_instance.id,
                new_status=StatusType.in_progress,
            )


class TestSubmissionOperations:
    """Tests for submission operations."""

    def test_submission_lifecycle(
        self,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        submission_data: dict[str, Any],
    ) -> None:
        """Test submission creation, update, and validation."""
        # Create submission
        submission = manual_task_instance_service.create_submission(
            instance_id=manual_task_instance.id,
            field_id=submission_data["field_id"],
            data=submission_data["data"],
        )
        assert submission.data == submission_data["data"]
        assert manual_task_instance.status == StatusType.in_progress

        # Update submission
        updated_data = {**submission_data["data"], "value": "updated"}
        updated = manual_task_instance_service.update_submission(
            instance_id=manual_task_instance.id,
            submission_id=submission.id,
            data=updated_data,
        )
        assert updated.data["value"] == "updated"

        # Test non-existent submission
        assert not manual_task_instance_service.get_submission_for_field(
            instance_id=manual_task_instance.id,
            field_id="non-existent",
        )


@pytest.mark.usefixtures("s3_client", "mock_s3_client")
class TestAttachmentOperations:
    """Tests for attachment operations."""

    def _add_attachment(
        self,
        db: Session,
        submission: ManualTaskSubmission,
        attachment_data: dict[str, Any],
    ) -> Attachment:
        """Helper to create and link an attachment."""
        attachment = Attachment.create_and_upload(
            db=db,
            data=attachment_data,
            attachment_file=BytesIO(b"test contents"),
        )
        AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment.id,
                "reference_id": submission.id,
                "reference_type": "manual_task_submission",
            },
        )
        return attachment

    def test_attachment_deletion_scenarios(
        self,
        manual_task_instance_service: ManualTaskInstanceService,
        attachment_field_submission: ManualTaskSubmission,
        attachment_data: dict[str, Any],
    ) -> None:
        """Test various attachment deletion scenarios."""
        db = manual_task_instance_service.db

        # Scenario 1: Delete non-last attachment
        attachment1 = self._add_attachment(
            db, attachment_field_submission, attachment_data
        )
        attachment2 = self._add_attachment(
            db, attachment_field_submission, attachment_data
        )
        assert len(attachment_field_submission.attachments) == 2

        manual_task_instance_service.delete_attachment_by_id(
            submission_id=attachment_field_submission.id,
            attachment_id=attachment1.id,
        )
        assert not db.query(Attachment).filter_by(id=attachment1.id).first()
        assert len(attachment_field_submission.attachments) == 1

        # Scenario 2: Delete last attachment
        manual_task_instance_service.delete_attachment_by_id(
            submission_id=attachment_field_submission.id,
            attachment_id=attachment2.id,
        )
        assert not db.query(Attachment).filter_by(id=attachment2.id).first()
        assert not db.query(ManualTaskSubmission).get(attachment_field_submission.id)


    def test_delete_attachment_by_id_error_cases(
        self,
        manual_task_instance_service: ManualTaskInstanceService,
        attachment_field_submission: ManualTaskSubmission,
        attachment_data: dict[str, Any],
    ) -> None:
        """Test error cases for delete_attachment_by_id."""
        with pytest.raises(ValueError, match="Submission with ID None does not exist"):
            manual_task_instance_service.delete_attachment_by_id(None, "some-id")

        with pytest.raises(
            ValueError,
            match=f"Attachment some-id not found in submission {attachment_field_submission.id}",
        ):
            manual_task_instance_service.delete_attachment_by_id(
                attachment_field_submission.id, "some-id"
            )


class TestTaskCompletion:
    """Tests for task completion."""

    def test_task_completion(
        self,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        submission_data: dict[str, Any],
    ) -> None:
        """Test task completion workflow."""
        # Submit required fields
        for field in manual_task_instance.config.field_definitions:
            if field.field_metadata.get("required"):
                submission_data["field_id"] = field.id
                submission_data["data"]["field_key"] = field.field_key
                submission_data["data"]["field_type"] = field.field_type
                manual_task_instance_service.create_submission(
                    instance_id=manual_task_instance.id,
                    field_id=field.id,
                    data=submission_data["data"],
                )

        # Complete task
        manual_task_instance_service.complete_task_instance(
            task_id=manual_task_instance.task_id,
            config_id=manual_task_instance.config_id,
            instance_id=manual_task_instance.id,
            user_id="test_user",
        )

        assert manual_task_instance.status == StatusType.completed
        assert manual_task_instance.completed_by_id == "test_user"
        assert any(
            "Completed task instance" in log.message
            for log in manual_task_instance.logs
        )

        # Verify completed instance validation
        with pytest.raises(StatusTransitionNotAllowed):
            manual_task_instance_service._get_instance(manual_task_instance.id)
