import time
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import pytest
from sqlalchemy.orm import Session

from fides.api.models.attachment import Attachment, AttachmentReference, AttachmentType
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
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.storage import StorageConfig
from fides.api.schemas.manual_tasks.manual_task_status import StatusType


@pytest.fixture
def mock_s3_client(s3_client, monkeypatch):
    """Fixture to mock the S3 client for attachment tests"""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr(
        "fides.api.service.storage.s3.get_s3_client", mock_get_s3_client
    )
    return s3_client


class TestManualTaskInstance:
    def test_create_manual_task_instance(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        privacy_request: PrivacyRequest,
    ):
        """Test creating a manual task instance."""
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_task_config.id,
                "entity_id": privacy_request.id,
                "entity_type": "privacy_request",
            },
        )

        assert instance.task_id == manual_task.id
        assert instance.config_id == manual_task_config.id
        assert instance.entity_id == privacy_request.id
        assert instance.entity_type == "privacy_request"
        assert instance.status == StatusType.pending
        assert instance.completed_at is None
        assert instance.completed_by_id is None
        assert instance.logs == []
        assert instance.submissions == []
        assert instance.config is manual_task_config
        assert instance.task is manual_task
        assert instance.attachments == []

    def test_required_fields(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
    ):
        """Test getting required fields."""
        # Update the field to be required
        manual_task_config_field_1.field_metadata = {"required": True}
        db.commit()

        required_fields = manual_task_instance.required_fields
        assert len(required_fields) == 1
        assert required_fields[0].id == manual_task_config_field_1.id
        assert required_fields[0].field_metadata["required"] is True

    def test_incomplete_fields(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
    ):
        """Test getting incomplete fields."""
        # Update the field to be required
        manual_task_config_field_1.field_metadata = {"required": True}
        db.commit()

        incomplete_fields = manual_task_instance.incomplete_fields
        assert len(incomplete_fields) == 1
        assert incomplete_fields[0].id == manual_task_config_field_1.id

    def test_completed_fields(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        user: FidesUser,
    ):
        """Test getting completed fields."""
        # Initially no completed fields
        assert len(manual_task_instance.completed_fields) == 0

        # Add a submission for field1
        ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {"value": "test"},
            },
        )

        # Now field1 should be completed
        completed_fields = manual_task_instance.completed_fields
        assert len(completed_fields) == 1
        assert completed_fields[0].id == manual_task_config_field_1.id

    @pytest.mark.usefixtures("mock_s3_client", "s3_client")
    def test_attachments(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        attachment_data: dict[str, Any],
        user: FidesUser,
    ):
        """Test getting attachments."""
        # Create a submission with an attachment
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {"value": "test"},
            },
        )

        # Create an attachment
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
                "reference_id": submission.id,
                "reference_type": "manual_task_submission",
            },
        )

        # Get attachments
        attachments = manual_task_instance.attachments
        assert len(attachments) == 1
        assert attachments[0].id == attachment.id
        assert attachments[0].file_name == "file.txt"

        attachment.delete(db)

    def test_status_transitions(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ):
        """Test status transitions."""
        # Initial status is pending
        assert manual_task_instance.status == StatusType.pending

        # Transition to in_progress
        manual_task_instance.update_status(db, StatusType.in_progress)
        assert manual_task_instance.status == StatusType.in_progress

        # Transition to completed
        manual_task_instance.mark_completed(db, "user1")
        assert manual_task_instance.status == StatusType.completed
        assert manual_task_instance.completed_at is not None
        assert manual_task_instance.completed_by_id == "user1"


class TestManualTaskSubmission:
    def test_create_manual_task_submission(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        user: FidesUser,
    ):
        """Test creating a manual task submission."""
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {"value": "test"},
            },
        )

        assert submission.task_id == manual_task_instance.task_id
        assert submission.config_id == manual_task_instance.config_id
        assert submission.field_id == manual_task_config_field_1.id
        assert submission.instance_id == manual_task_instance.id
        assert submission.submitted_by == user.id
        assert submission.data == {"value": "test"}
        assert submission.submitted_at is not None

    def test_update_manual_task_submission(
        self, db: Session, manual_task_submission: ManualTaskSubmission
    ):
        """Test updating a manual task submission."""
        updated_data = {"value": "updated test"}
        updated_submission = manual_task_submission.update(
            db=db,
            data={
                "id": manual_task_submission.id,
                "data": updated_data,
            },
        )

        assert updated_submission.id == manual_task_submission.id
        assert updated_submission.data == updated_data
        assert updated_submission.updated_at > manual_task_submission.submitted_at

    def test_submission_relationships(
        self, db: Session, manual_task_submission: ManualTaskSubmission
    ):
        """Test submission relationships."""
        # Test task relationship
        assert manual_task_submission.task is not None
        assert manual_task_submission.task.id == manual_task_submission.task_id

        # Test config relationship
        assert manual_task_submission.config is not None
        assert manual_task_submission.config.id == manual_task_submission.config_id

        # Test field relationship
        assert manual_task_submission.field is not None
        assert manual_task_submission.field.id == manual_task_submission.field_id

        # Test instance relationship
        assert manual_task_submission.instance is not None
        assert manual_task_submission.instance.id == manual_task_submission.instance_id

    @pytest.mark.usefixtures("mock_s3_client", "s3_client")
    def test_submission_attachments(
        self,
        db: Session,
        manual_task_submission: ManualTaskSubmission,
        attachment_data: dict[str, Any],
    ):
        """Test submission attachments."""
        # Create an attachment
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

        # Verify attachment relationship
        assert len(manual_task_submission.attachments) == 1
        assert manual_task_submission.attachments[0].id == attachment.id
        assert manual_task_submission.attachments[0].file_name == "file.txt"

        attachment.delete(db)

    def test_submission_data_validation(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        user: FidesUser,
    ):
        """Test submission data validation."""
        # Test with valid data
        valid_submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {"value": "test"},
            },
        )
        assert valid_submission is not None

        # Test with empty data
        # with pytest.raises(Exception):
        ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {},
            },
        )

    def test_submission_cascade_delete(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        user: FidesUser,
    ):
        """Test that submissions are deleted when instance is deleted."""
        # Create a submission
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {"value": "test"},
            },
        )

        # Delete the instance
        db.delete(manual_task_instance)
        db.commit()

        # Verify submission is deleted
        deleted_submission = (
            db.query(ManualTaskSubmission).filter_by(id=submission.id).first()
        )
        assert deleted_submission is None

    def test_submission_timestamps(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        user: FidesUser,
    ):
        """Test submission timestamp handling."""
        # Create initial submission
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {"value": "test"},
            },
        )
        initial_submitted_at = submission.submitted_at
        initial_updated_at = submission.updated_at

        # Add a small delay to ensure timestamp difference
        time.sleep(0.1)

        # Update submission
        updated_submission = submission.update(
            db=db,
            data={
                "data": {"value": "updated"},
            },
        )

        # Verify timestamps
        assert (
            updated_submission.submitted_at == initial_submitted_at
        )  # submitted_at should not change
        assert (
            updated_submission.updated_at > initial_updated_at
        )  # only updated_at should change
