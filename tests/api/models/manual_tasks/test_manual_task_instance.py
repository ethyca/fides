import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_instance import ManualTaskInstance, ManualTaskSubmission
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.attachment import Attachment, AttachmentReference
from fides.api.schemas.manual_tasks.manual_task_schemas import StatusType



def test_create_manual_task_instance(db: Session, manual_task: ManualTask, manual_task_config: ManualTaskConfig, privacy_request: PrivacyRequest):
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
    assert instance.logs is None
    assert instance.submissions is None
    assert instance.config is manual_task_config
    assert instance.task is manual_task
    assert instance.attachments is None


def test_required_fields(manual_task_instance: ManualTaskInstance):
    """Test getting required fields."""
    required_fields = manual_task_instance.required_fields
    assert len(required_fields) == 1
    assert required_fields[0].id == "field1"
    assert required_fields[0].required is True


def test_incomplete_fields(manual_task_instance: ManualTaskInstance):
    """Test getting incomplete fields."""
    incomplete_fields = manual_task_instance.incomplete_fields
    assert len(incomplete_fields) == 1
    assert incomplete_fields[0].id == "field1"


def test_completed_fields(db: Session, manual_task_instance: ManualTaskInstance):
    """Test getting completed fields."""
    # Initially no completed fields
    assert len(manual_task_instance.completed_fields) == 0

    # Add a submission for field1
    ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "field_id": "field1",
            "instance_id": manual_task_instance.id,
            "submitted_by": 1,
            "data": {"value": "test"},
        },
    )

    # Now field1 should be completed
    completed_fields = manual_task_instance.completed_fields
    assert len(completed_fields) == 1
    assert completed_fields[0].id == "field1"


def test_attachments(db: Session, manual_task_instance: ManualTaskInstance):
    """Test getting attachments."""
    # Create a submission with an attachment
    submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "field_id": "field1",
            "instance_id": manual_task_instance.id,
            "submitted_by": 1,
            "data": {"value": "test"},
        },
    )

    # Create an attachment
    attachment = Attachment.create(
        db=db,
        data={
            "name": "test.txt",
            "content_type": "text/plain",
            "size": 100,
        },
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
    attachments = manual_task_instance.attachments(db)
    assert len(attachments) == 1
    assert attachments[0].id == attachment.id
    assert attachments[0].name == "test.txt"


def test_status_transitions(db: Session, manual_task_instance: ManualTaskInstance):
    """Test status transitions."""
    # Initial status is pending
    assert manual_task_instance.status == StatusType.pending

    # Transition to in_progress
    manual_task_instance.transition_status(db, StatusType.in_progress)
    assert manual_task_instance.status == StatusType.in_progress

    # Transition to completed
    manual_task_instance.transition_status(
        db, StatusType.completed, completed_by_id="user1"
    )
    assert manual_task_instance.status == StatusType.completed
    assert manual_task_instance.completed_at is not None
    assert manual_task_instance.completed_by_id == "user1"

    # Verify status is recorded in logs
    logs = manual_task_instance.logs
    assert len(logs) == 2  # Two transitions
    assert logs[0].status == StatusType.in_progress
    assert logs[1].status == StatusType.completed


def test_create_manual_task_submission(db: Session, manual_task_instance: ManualTaskInstance):
    """Test creating a manual task submission."""
    submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "field_id": "field1",
            "instance_id": manual_task_instance.id,
            "submitted_by": 1,
            "data": {"value": "test"},
        },
    )

    assert submission.task_id == manual_task_instance.task_id
    assert submission.config_id == manual_task_instance.config_id
    assert submission.field_id == "field1"
    assert submission.instance_id == manual_task_instance.id
    assert submission.submitted_by == 1
    assert submission.data == {"value": "test"}
    assert submission.submitted_at is not None


def test_update_manual_task_submission(db: Session, manual_task_submission: ManualTaskSubmission):
    """Test updating a manual task submission."""
    updated_data = {"value": "updated test"}
    updated_submission = ManualTaskSubmission.update(
        db=db,
        data={
            "id": manual_task_submission.id,
            "data": updated_data,
        },
    )

    assert updated_submission.id == manual_task_submission.id
    assert updated_submission.data == updated_data
    assert updated_submission.submitted_at > manual_task_submission.submitted_at


def test_submission_relationships(db: Session, manual_task_submission: ManualTaskSubmission):
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


def test_submission_attachments(db: Session, manual_task_submission: ManualTaskSubmission):
    """Test submission attachments."""
    # Create an attachment
    attachment = Attachment.create(
        db=db,
        data={
            "name": "test.txt",
            "content_type": "text/plain",
            "size": 100,
        },
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
    assert manual_task_submission.attachments[0].name == "test.txt"


def test_submission_data_validation(db: Session, manual_task_instance: ManualTaskInstance):
    """Test submission data validation."""
    # Test with valid data
    valid_submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "field_id": "field1",
            "instance_id": manual_task_instance.id,
            "submitted_by": 1,
            "data": {"value": "test"},
        },
    )
    assert valid_submission is not None

    # Test with empty data
    with pytest.raises(Exception):
        ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task_instance.task_id,
                "config_id": manual_task_instance.config_id,
                "field_id": "field1",
                "instance_id": manual_task_instance.id,
                "submitted_by": 1,
                "data": {},
            },
        )


def test_submission_cascade_delete(db: Session, manual_task_instance: ManualTaskInstance):
    """Test that submissions are deleted when instance is deleted."""
    # Create a submission
    submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "field_id": "field1",
            "instance_id": manual_task_instance.id,
            "submitted_by": 1,
            "data": {"value": "test"},
        },
    )

    # Delete the instance
    db.delete(manual_task_instance)
    db.commit()

    # Verify submission is deleted
    deleted_submission = db.query(ManualTaskSubmission).filter_by(id=submission.id).first()
    assert deleted_submission is None


def test_submission_timestamps(db: Session, manual_task_instance: ManualTaskInstance):
    """Test submission timestamp handling."""
    # Create initial submission
    submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task_instance.task_id,
            "config_id": manual_task_instance.config_id,
            "field_id": "field1",
            "instance_id": manual_task_instance.id,
            "submitted_by": 1,
            "data": {"value": "test"},
        },
    )
    initial_submitted_at = submission.submitted_at

    # Update submission
    updated_submission = ManualTaskSubmission.update(
        db=db,
        data={
            "id": submission.id,
            "data": {"value": "updated"},
        },
    )

    # Verify timestamps
    assert updated_submission.submitted_at > initial_submitted_at
    assert updated_submission.updated_at > initial_submitted_at
