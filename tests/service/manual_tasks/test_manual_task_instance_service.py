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
        f for f in manual_task_instance.config.field_definitions
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
def attachment(
    db: Session,
    manual_task_submission: ManualTaskSubmission,
    attachment_data: dict[str, Any],
) -> Generator[Attachment, None, None]:
    """Fixture for a file attachment."""
    attachment = Attachment.create_and_upload(
        db=db,
        data=attachment_data,
        attachment_file=BytesIO(b"test contents"),
    )
    AttachmentReference.create(
        db=db,
        data={
            "attachment_id": attachment.id,
            "reference_id": manual_task_submission.id,
            "reference_type": "manual_task_submission",
        },
    )
    yield attachment
    attachment.delete(db)


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

    def test_attachment_deletion(
        self,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_submission: ManualTaskSubmission,
        attachment: Attachment,
        attachment_data: dict[str, Any],
    ) -> None:
        """Test attachment deletion scenarios."""
        submission_id = manual_task_submission.id

        # Test single attachment deletion
        manual_task_instance_service.delete_attachment_by_id(
            submission_id=submission_id,
            attachment_id=attachment.id,
        )

        # Verify attachment is deleted
        assert not manual_task_instance_service.db.query(Attachment).filter_by(
            id=attachment.id
        ).first()

        # Verify submission is deleted (since it was the only attachment)
        assert not manual_task_instance_service.db.query(ManualTaskSubmission).filter_by(
            id=submission_id
        ).first()

        # Test error cases
        with pytest.raises(ValueError, match="Submission with ID None does not exist"):
            manual_task_instance_service.delete_attachment_by_id(
                submission_id=None,
                attachment_id="some-id",
            )

        # Create a new submission for testing non-existent attachment
        new_submission = ManualTaskSubmission.create(
            manual_task_instance_service.db,
            data=submission_data(manual_task_submission.instance, None, "attachment"),
        )
        with pytest.raises(ValueError, match=f"Attachment some-id not found in submission {new_submission.id}"):
            manual_task_instance_service.delete_attachment_by_id(
                submission_id=new_submission.id,
                attachment_id="some-id",
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
