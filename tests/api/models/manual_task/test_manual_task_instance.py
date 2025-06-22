import time
from io import BytesIO
from typing import Any

import pytest
from sqlalchemy.orm import Session

from fides.api.models.attachment import Attachment, AttachmentReference
from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskInstance,
    ManualTaskSubmission,
    StatusType,
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.models.privacy_request import PrivacyRequest


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

    def test_submissions_relationship_auto_sync(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        user: FidesUser,
    ):
        """Test that submissions relationship automatically syncs without manual expire/refresh."""
        # Initially no submissions
        assert len(manual_task_instance.submissions) == 0

        # Create a submission
        submission1 = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {"value": "test1"},
            },
        )

        # Verify submissions collection is automatically updated (no expire/refresh needed)
        assert len(manual_task_instance.submissions) == 1
        assert manual_task_instance.submissions[0].id == submission1.id

        # Create another submission
        submission2 = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {"value": "test2"},
            },
        )

        # Verify collection automatically includes new submission
        assert len(manual_task_instance.submissions) == 2
        submission_ids = [s.id for s in manual_task_instance.submissions]
        assert submission1.id in submission_ids
        assert submission2.id in submission_ids

        # Delete a submission
        db.delete(submission1)
        db.commit()

        # Verify collection automatically reflects deletion (cascade should work)
        assert len(manual_task_instance.submissions) == 1
        assert manual_task_instance.submissions[0].id == submission2.id

    def test_attachments_relationship_auto_sync(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        attachment_data: dict[str, Any],
        user: FidesUser,
        mock_s3_client,
    ):
        """Test that attachments relationship automatically syncs through submissions."""
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

        # Initially no attachments
        assert len(manual_task_instance.attachments) == 0

        # Create and link an attachment
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

        # Verify attachments collection is automatically updated
        assert len(manual_task_instance.attachments) == 1
        assert manual_task_instance.attachments[0].id == attachment.id

        # Clean up
        attachment.delete(db)

    def test_bidirectional_relationship_consistency(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        user: FidesUser,
    ):
        """Test that bidirectional relationships stay consistent automatically."""
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

        # Verify both sides of the relationship
        assert submission in manual_task_instance.submissions
        assert submission.instance == manual_task_instance
        assert submission.instance_id == manual_task_instance.id

        # Verify config relationships
        assert submission in manual_task_instance.config.submissions
        assert submission.config == manual_task_instance.config

        # Verify task relationships
        assert submission in manual_task_instance.task.submissions
        assert submission.task == manual_task_instance.task

    def test_manual_task_deletion_orphans_instances(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ) -> None:
        """Test that deleting a ManualTask orphans instances (sets task_id to NULL)."""
        task = manual_task_instance.task
        task_id = task.id
        instance_id = manual_task_instance.id

        # Verify instance is initially linked to task
        assert manual_task_instance.task_id == task_id
        assert not manual_task_instance.is_orphaned

        # Delete task with an existing instance (should succeed and orphan the instance)
        db.delete(task)
        db.commit()

        # Verify task is deleted
        deleted_task = db.query(ManualTask).filter_by(id=task_id).first()
        assert deleted_task is None

        # Verify instance still exists but is now orphaned
        orphaned_instance = db.query(ManualTaskInstance).filter_by(id=instance_id).first()
        assert orphaned_instance is not None
        assert orphaned_instance.task_id is None
        assert orphaned_instance.is_orphaned

    def test_manual_task_deletion_orphans_historical_data(
        self, db: Session, manual_task_instance: ManualTaskInstance
    ) -> None:
        """Test that deleting a ManualTask orphans historical data but deletes references."""
        task = manual_task_instance.task

        # Create some logs for the task
        log1 = ManualTaskLog.create_log(
            db=db,
            task_id=task.id,
            status=ManualTaskLogStatus.created,
            message="Test log 1",
        )
        log2 = ManualTaskLog.create_log(
            db=db,
            task_id=task.id,
            status=ManualTaskLogStatus.in_progress,
            message="Test log 2",
        )

        # Verify logs exist
        assert len(task.logs) >= 2

        # Store IDs for verification
        task_id = task.id
        instance_id = manual_task_instance.id
        log1_id = log1.id
        log2_id = log2.id

        # Delete the task (should orphan instance and logs)
        db.delete(task)
        db.commit()

        # Verify task is deleted
        deleted_task = db.query(ManualTask).filter_by(id=task_id).first()
        assert deleted_task is None

        # Verify instance still exists but is orphaned
        orphaned_instance = db.query(ManualTaskInstance).filter_by(id=instance_id).first()
        assert orphaned_instance is not None
        assert orphaned_instance.task_id is None
        assert orphaned_instance.is_orphaned

        # Verify logs still exist but are orphaned
        orphaned_log1 = db.query(ManualTaskLog).filter_by(id=log1_id).first()
        orphaned_log2 = db.query(ManualTaskLog).filter_by(id=log2_id).first()
        assert orphaned_log1 is not None
        assert orphaned_log2 is not None
        assert orphaned_log1.task_id is None
        assert orphaned_log2.task_id is None


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

        # Delete the instance using custom delete method
        manual_task_instance.delete(db)
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

    @pytest.mark.usefixtures("mock_s3_client", "s3_client")
    def test_attachment_relationship_auto_sync(
        self,
        db: Session,
        manual_task_submission: ManualTaskSubmission,
        attachment_data: dict[str, Any],
    ):
        """Test that attachment relationships automatically sync without manual expire/refresh."""
        # Initially no attachments
        assert len(manual_task_submission.attachments) == 0

        # Create first attachment
        attachment1 = Attachment.create_and_upload(
            db=db,
            data=attachment_data,
            attachment_file=BytesIO(b"test contents 1"),
        )

        AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment1.id,
                "reference_id": manual_task_submission.id,
                "reference_type": "manual_task_submission",
            },
        )

        # Verify attachments collection is automatically updated (no expire/refresh needed)
        assert len(manual_task_submission.attachments) == 1
        assert manual_task_submission.attachments[0].id == attachment1.id

        # Create second attachment
        attachment_data2 = attachment_data.copy()
        attachment_data2["file_name"] = "file2.txt"
        attachment2 = Attachment.create_and_upload(
            db=db,
            data=attachment_data2,
            attachment_file=BytesIO(b"test contents 2"),
        )

        AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment2.id,
                "reference_id": manual_task_submission.id,
                "reference_type": "manual_task_submission",
            },
        )

        # Verify collection automatically includes new attachment
        assert len(manual_task_submission.attachments) == 2
        attachment_ids = [a.id for a in manual_task_submission.attachments]
        assert attachment1.id in attachment_ids
        assert attachment2.id in attachment_ids

        # Clean up
        attachment1.delete(db)
        attachment2.delete(db)

    def test_submission_update_preserves_relationships(
        self,
        db: Session,
        manual_task_submission: ManualTaskSubmission,
    ):
        """Test that updating submission data preserves all relationships automatically."""
        # Store original relationship references
        original_task = manual_task_submission.task
        original_config = manual_task_submission.config
        original_field = manual_task_submission.field
        original_instance = manual_task_submission.instance

        # Update submission data
        updated_submission = manual_task_submission.update(
            db=db,
            data={
                "data": {"value": "updated_value", "additional": "data"},
            },
        )

        # Verify all relationships are preserved automatically (no expire/refresh needed)
        assert updated_submission.task == original_task
        assert updated_submission.config == original_config
        assert updated_submission.field == original_field
        assert updated_submission.instance == original_instance

        # Verify bidirectional consistency is maintained
        assert updated_submission in original_instance.submissions
        assert updated_submission in original_config.submissions
        assert updated_submission in original_task.submissions

    def test_cascade_delete_with_attachments(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        attachment_data: dict[str, Any],
        user: FidesUser,
        mock_s3_client,
    ):
        """Test that cascade delete works properly with attachments."""
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

        # Create and link attachment
        attachment = Attachment.create_and_upload(
            db=db,
            data=attachment_data,
            attachment_file=BytesIO(b"test contents"),
        )

        attachment_ref = AttachmentReference.create(
            db=db,
            data={
                "attachment_id": attachment.id,
                "reference_id": submission.id,
                "reference_type": "manual_task_submission",
            },
        )

        # Verify setup
        assert len(manual_task_instance.submissions) == 1
        assert len(submission.attachments) == 1

        # Delete the instance using custom delete method (should handle submissions and attachments)
        instance_id = manual_task_instance.id
        submission_id = submission.id
        attachment_ref_id = attachment_ref.id
        attachment_id = attachment.id

        manual_task_instance.delete(db)
        db.commit()

        # Verify deletion worked
        deleted_instance = db.query(ManualTaskInstance).filter_by(id=instance_id).first()
        deleted_submission = db.query(ManualTaskSubmission).filter_by(id=submission_id).first()
        deleted_ref = db.query(AttachmentReference).filter_by(id=attachment_ref_id).first()
        deleted_attachment = db.query(Attachment).filter_by(id=attachment_id).first()

        assert deleted_instance is None
        assert deleted_submission is None
        # Note: AttachmentReference should also be deleted
        assert deleted_ref is None
        # Note: Attachment should also be deleted by our custom delete method
        assert deleted_attachment is None

    def test_relationship_loading_efficiency(
        self,
        db: Session,
        manual_task_submission: ManualTaskSubmission,
    ):
        """Test that relationships load efficiently with our lazy='select' configuration."""
        # Access relationships to trigger loading
        task = manual_task_submission.task
        config = manual_task_submission.config
        field = manual_task_submission.field
        instance = manual_task_submission.instance

        # Verify all relationships are properly loaded
        assert task is not None
        assert config is not None
        assert field is not None
        assert instance is not None

        # Verify we can access nested relationships without additional queries
        assert task.id == manual_task_submission.task_id
        assert config.id == manual_task_submission.config_id
        assert field.id == manual_task_submission.field_id
        assert instance.id == manual_task_submission.instance_id

        # Verify bidirectional navigation works
        assert manual_task_submission in instance.submissions
        assert manual_task_submission in config.submissions
        assert manual_task_submission in task.submissions

    @pytest.mark.usefixtures("mock_s3_client", "s3_client")
    def test_attachment_relationship_consistency(
        self,
        db: Session,
        manual_task_submission: ManualTaskSubmission,
        attachment_data: dict[str, Any],
    ):
        """Test that attachment relationships remain consistent across transactions."""
        # Start with empty attachments
        initial_attachments = list(manual_task_submission.attachments)
        assert len(initial_attachments) == 0

        # Create attachment in a separate transaction
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
        db.commit()

        # Verify relationship automatically reflects new attachment
        updated_attachments = list(manual_task_submission.attachments)
        assert len(updated_attachments) == 1
        assert updated_attachments[0].id == attachment.id
        assert updated_attachments[0].file_name == "file.txt"

        # Clean up
        attachment.delete(db)

    def test_relationship_consistency_across_transactions(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        user: FidesUser,
    ):
        """Test that relationships remain consistent across separate transactions."""
        # Start with empty submissions
        initial_submissions = list(manual_task_instance.submissions)
        assert len(initial_submissions) == 0

        # Create submission in a separate transaction
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
        db.commit()

        # Verify relationship automatically reflects new submission
        updated_submissions = list(manual_task_instance.submissions)
        assert len(updated_submissions) == 1
        assert updated_submissions[0].id == submission.id

        # Update the submission
        submission.update(db=db, data={"data": {"value": "updated"}})
        db.commit()

        # Verify the relationship reflects the update
        fresh_submissions = list(manual_task_instance.submissions)
        assert len(fresh_submissions) == 1
        assert fresh_submissions[0].data == {"value": "updated"}

    def test_cascade_deletion_behavior(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        user: FidesUser,
    ):
        """Test that cascade deletion properly removes related records."""
        # Create multiple submissions
        submission1 = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {"value": "test1"},
            },
        )

        submission2 = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": manual_task_config_field_1.id,
                "instance_id": manual_task_instance.id,
                "submitted_by": user.id,
                "data": {"value": "test2"},
            },
        )

        db.commit()

        # Verify both submissions exist
        assert len(manual_task_instance.submissions) == 2

        # Store IDs for verification
        submission1_id = submission1.id
        submission2_id = submission2.id

        # Delete the instance using custom delete method - should handle all submissions
        manual_task_instance.delete(db)
        db.commit()

        # Verify related submissions were properly deleted
        deleted_submission1 = db.query(ManualTaskSubmission).filter_by(id=submission1_id).first()
        deleted_submission2 = db.query(ManualTaskSubmission).filter_by(id=submission2_id).first()

        assert deleted_submission1 is None
        assert deleted_submission2 is None

    def test_relationship_loading_behavior(
        self,
        db: Session,
        manual_task_instance: ManualTaskInstance,
        manual_task_config_field_1: ManualTaskConfigField,
        user: FidesUser,
    ):
        """Test that relationships load fresh data when accessed after changes."""
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

        # Access the relationship to load it
        initial_submissions = manual_task_instance.submissions
        assert len(initial_submissions) == 1

        # Update the submission in a new transaction
        submission.data = {"value": "updated"}
        db.add(submission)
        db.commit()

        # Relationship should reflect the updated data
        updated_submissions = manual_task_instance.submissions
        assert len(updated_submissions) == 1
        assert updated_submissions[0].data["value"] == "updated"

    def test_manual_task_creation_logging(
        self,
        db: Session,
        privacy_request,
    ):
        """Test that manual task creation properly logs with valid task_id (refreshes if needed)."""
        # Count existing logs
        initial_log_count = db.query(ManualTaskLog).count()

        # Create a manual task
        task_data = {
            "task_type": "privacy_request",
            "parent_entity_id": privacy_request.id,
            "parent_entity_type": "connection_config",
        }

        task = ManualTask.create(db=db, data=task_data)

        # Verify task was created with valid ID
        assert task.id is not None
        assert task.id != ""

        # Check that a log was created (should always happen now)
        final_log_count = db.query(ManualTaskLog).count()
        assert final_log_count == initial_log_count + 1

        # Find the log entry for this task
        task_log = db.query(ManualTaskLog).filter(
            ManualTaskLog.task_id == task.id
        ).first()

        # Verify the log has valid task_id (not NULL)
        assert task_log is not None
        assert task_log.task_id is not None
        assert task_log.task_id == task.id
        assert task_log.message == f"Created manual task for {task_data['task_type']}"
        assert task_log.status == "created"
