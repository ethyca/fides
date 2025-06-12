from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Generator

import pytest
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
    StatusType,
    StatusTransitionNotAllowed,
)
from fides.service.manual_tasks.manual_task_instance_service import (
    ManualTaskInstanceService,
)
from tests.service.manual_tasks.conftest import TEXT_FIELD_KEY, CHECKBOX_FIELD_KEY, ATTACHMENT_FIELD_KEY


@pytest.fixture
def attachment(db: Session, manual_task_submission: ManualTaskSubmission, attachment_data: dict[str, Any]):
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
            "reference_id": manual_task_submission.id,
            "reference_type": "manual_task_submission",
        },
    )
    yield attachment
    attachment.delete(db)

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
    manual_task_config_field_1: ManualTaskConfigField,
    respondent_user: FidesUser,
):
    submission = ManualTaskSubmission.create(
        db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "instance_id": manual_task_instance.id,
            "field_id": manual_task_config_field_1.id,
            "submitted_by": respondent_user.id,
            "data": {
                "field_key": TEXT_FIELD_KEY,
                "field_type": "text",
                "value": "test value",
            },
        }
    )
    yield submission
    submission.delete(db)

@pytest.fixture
def manual_task_submission_checkbox(
    db: Session,
    manual_task_instance: ManualTaskInstance,
    manual_task_config_field_2: ManualTaskConfigField,
    respondent_user: FidesUser,
):
    submission = ManualTaskSubmission.create(
        db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "instance_id": manual_task_instance.id,
            "field_id": next(
                field for field in manual_task_instance.config.field_definitions
                if field.field_key == CHECKBOX_FIELD_KEY
                ).id,
            "submitted_by": respondent_user.id,
            "data": {
                "field_key": CHECKBOX_FIELD_KEY,
                "field_type": "checkbox",
                "value": True,
            },
        }
    )
    yield submission
    submission.delete(db)

@pytest.fixture
def manual_task_submission_attachment(
    db: Session,
    manual_task_instance: ManualTaskInstance,
    manual_task_config_field_3: ManualTaskConfigField,
    respondent_user: FidesUser,
):
    submission = ManualTaskSubmission.create(
        db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "instance_id": manual_task_instance.id,
            "field_id": next(
                field for field in manual_task_instance.config.field_definitions
                if field.field_key == ATTACHMENT_FIELD_KEY
            ).id,
            "submitted_by": respondent_user.id,
            "data": {
                "field_key": ATTACHMENT_FIELD_KEY,
                "field_type": "attachment",
                "value": "test value",
            },
        }
    )
    yield submission
    submission.delete(db)



class TestManualTaskInstanceService:
    """Test suite for ManualTaskInstanceService."""

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

    def test_update_status(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
    ) -> None:
        """Test updating instance status."""
        manual_task_instance_service.update_status(
            db=db,
            instance_id=manual_task_instance.id,
            new_status=StatusType.in_progress,
            user_id="test_user",
        )

        assert manual_task_instance.status == StatusType.in_progress

        # Verify log was created
        log = manual_task_instance.logs[-1]
        assert log.status == ManualTaskLogStatus.in_processing
        assert "status transitioning" in log.message

    def test_create_submission(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
    ) -> None:
        """Test creating a submission."""
        data = {
            "field_key": manual_task_config_field_1.field_key,
            "field_type": manual_task_config_field_1.field_type,
            "value": "test value",
        }

        submission = manual_task_instance_service.create_submission(
            instance=manual_task_instance,
            field=manual_task_config_field_1,
            data=data,
        )

        assert submission.instance_id == manual_task_instance.id
        assert submission.field_id == manual_task_config_field_1.id
        assert submission.data == data

        # Verify instance status was updated
        assert manual_task_instance.status == StatusType.in_progress

        # Verify log was created
        log = manual_task_instance.logs[-1]
        assert log.status == ManualTaskLogStatus.complete
        assert "Created submission" in log.message

    def test_update_submission(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
    ) -> None:
        """Test updating a submission."""
        # First create a submission
        initial_data = {
            "field_key": manual_task_config_field_1.field_key,
            "field_type": manual_task_config_field_1.field_type,
            "value": "initial value",
        }
        submission = manual_task_instance_service.create_submission(
            instance=manual_task_instance,
            field=manual_task_config_field_1,
            data=initial_data,
        )

        # Then update it
        updated_data = {
            "field_key": manual_task_config_field_1.field_key,
            "field_type": manual_task_config_field_1.field_type,
            "value": "updated value",
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "instance_id": manual_task_instance.id,
            "submitted_by": 1,
        }

        updated_submission = manual_task_instance_service.update_submission(
            instance=manual_task_instance,
            submission=submission,
            data=updated_data,
        )

        assert updated_submission.data == updated_data

        # Verify log was created
        log = manual_task_instance.logs[-1]
        assert log.status == ManualTaskLogStatus.complete
        assert "Updated submission" in log.message

    def test_create_or_update_submission_new(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
    ) -> None:
        """Test create_or_update_submission when submission doesn't exist."""
        data = {
            "field_key": manual_task_config_field_1.field_key,
            "field_type": manual_task_config_field_1.field_type,
            "value": "test value",
        }

        submission = manual_task_instance_service.create_or_update_submission(
            instance_id=manual_task_instance.id,
            field_id=manual_task_config_field_1.id,
            data=data,
        )

        assert submission.instance_id == manual_task_instance.id
        assert submission.field_id == manual_task_config_field_1.id
        assert submission.data == data

    def test_create_or_update_submission_existing(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
    ) -> None:
        """Test create_or_update_submission when submission exists."""
        # First create a submission
        initial_data = {
            "field_key": manual_task_config_field_1.field_key,
            "field_type": manual_task_config_field_1.field_type,
            "value": "initial value",
        }
        manual_task_instance_service.create_submission(
            instance=manual_task_instance,
            field=manual_task_config_field_1,
            data=initial_data,
        )

        # Then update it using create_or_update
        updated_data = {
            "field_key": manual_task_config_field_1.field_key,
            "field_type": manual_task_config_field_1.field_type,
            "value": "updated value",
        }

        submission = manual_task_instance_service.create_or_update_submission(
            instance_id=manual_task_instance.id,
            field_id=manual_task_config_field_1.id,
            data=updated_data,
        )

        assert submission.data == updated_data

    def test_complete_task_instance(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
    ) -> None:
        """Test completing a task instance."""
        manual_task_instance_service.complete_task_instance(
            instance_id=manual_task_instance.id,
            user_id="test_user",
        )

        assert manual_task_instance.status == StatusType.completed
        assert manual_task_instance.completed_by_id == "test_user"
        assert manual_task_instance.completed_at is not None

        # Verify log was created
        log = manual_task_instance.logs[-1]
        assert log.status == ManualTaskLogStatus.complete
        assert "completed by user" in log.message

    def test_validate_instance_for_submission_completed(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
    ) -> None:
        """Test validation fails for completed instance."""
        manual_task_instance_service.complete_task_instance(
            instance_id=manual_task_instance.id,
            user_id="test_user",
        )

        with pytest.raises(StatusTransitionNotAllowed, match="is already completed"):
            manual_task_instance_service._validate_instance_for_submission(
                manual_task_instance.id
            )

    def test_validate_field_for_submission_mismatch(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_config_field_1: ManualTaskConfigField,
    ) -> None:
        """Test validation fails for field mismatch."""
        data = {
            "field_key": "wrong_key",
            "field_type": manual_task_config_field_1.field_type,
            "value": "test value",
        }

        with pytest.raises(
            ValueError, match="Provided field id does not match field key"
        ):
            manual_task_instance_service._validate_field_for_submission(
                manual_task_config_field_1.id, data
            )

    def test_delete_attachment_by_id_single_attachment(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        submission: ManualTaskSubmission,
        attachment: Attachment,
        attachment_data: dict[str, Any],
    ) -> None:
        """Test deleting the only attachment for a submission."""

        # Delete the attachment
        manual_task_instance_service.delete_attachment_by_id(
            instance_id=manual_task_instance.id,
            field_id=manual_task_config_field_1.id,
            submission_id=None,
            attachment_id=attachment.id,
        )

        # Verify submission was deleted
        assert (
            db.query(ManualTaskSubmission).filter_by(id=submission.id).first() is None
        )

    @pytest.mark.usefixtures("mock_s3_client", "s3_client")
    def test_delete_attachment_by_id_multiple_attachments(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        manual_task_submission: ManualTaskSubmission,
        respondent_user: FidesUser,
        attachment: Attachment,
        attachment_data: dict[str, Any],
    ) -> None:
        """Test deleting one of multiple attachments for a submission."""
        # Create a submission with multiple attachments


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
                "reference_id": manual_task_submission.id,
                "reference_type": "manual_task_submission",
            },
        )

        # Delete one attachment
        manual_task_instance_service.delete_attachment_by_id(
            instance_id=manual_task_instance.id,
            field_id=manual_task_config_field_1.id,
            submission_id=None,
            attachment_id=attachment.id,
        )

        # Verify only one attachment was deleted
        assert db.query(Attachment).filter_by(id=attachment.id).first() is None
        assert db.query(Attachment).filter_by(id=attachment2.id).first() is not None
        assert (
            db.query(ManualTaskSubmission).filter_by(id=manual_task_submission.id).first()
            is not None
        )
        assert len(manual_task_submission.attachments) == 1
        assert manual_task_submission.attachments[0].id == attachment2.id

    def test_delete_attachment_by_id_completed_instance(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        attachment: Attachment,
    ) -> None:
        """Test deleting attachment fails for completed instance."""
        # Create a submission with an attachment
        data = {
            "field_key": manual_task_config_field_1.field_key,
            "field_type": manual_task_config_field_1.field_type,
            "value": "test value",
        }
        submission = manual_task_instance_service.create_submission(
            instance=manual_task_instance,
            field=manual_task_config_field_1,
            data=data,
        )

        # Complete the instance
        manual_task_instance_service.complete_task_instance(
            instance_id=manual_task_instance.id,
            user_id="test_user",
        )

        # Try to delete the attachment
        with pytest.raises(ValueError, match="is already completed"):
            manual_task_instance_service.delete_attachment_by_id(
                instance_id=manual_task_instance.id,
                field_id=manual_task_config_field_1.id,
                submission_id=None,
                attachment_id=attachment.id,
            )

    def test_delete_attachment_by_id_invalid_attachment(
        self,
        db: Session,
        manual_task_instance_service: ManualTaskInstanceService,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        manual_task_submission: ManualTaskSubmission,
    ) -> None:
        """Test deleting non-existent attachment."""
        # Create a submission


        # Try to delete the unlinked attachment
        with pytest.raises(ValueError, match="not found for submission"):
            manual_task_instance_service.delete_attachment_by_id(
                instance_id=manual_task_instance.id,
                field_id=manual_task_config_field_1.id,
                submission_id=manual_task_submission.id,
                attachment_id = "invalid-attachment-id"
            )
