from unittest.mock import create_autospec

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.digest.digest_config import DigestConfig
from fides.api.models.digest.digest_execution import DigestTaskExecution
from fides.api.models.worker_task import ExecutionLogStatus


def assert_default_values(execution: DigestTaskExecution):
    assert execution.id is not None
    assert execution.status == ExecutionLogStatus.pending
    assert execution.processed_recipients == 0
    assert execution.successful_communications == 0
    assert execution.failed_communications == 0
    assert execution.execution_state == {}
    assert execution.processed_user_ids == []
    assert execution.started_at is None
    assert execution.completed_at is None
    assert execution.last_checkpoint_at is None
    assert execution.error_message is None
    assert execution.created_at is not None
    assert execution.updated_at is not None


@pytest.fixture
def digest_execution(db: Session, digest_config: DigestConfig):
    """Create a test digest execution."""
    execution = DigestTaskExecution.create(
        db=db,
        data={
            "digest_config_id": digest_config.id,
            "action_type": "digest_processing",
            "total_recipients": 100,
            "status": ExecutionLogStatus.pending,
        },
    )
    yield execution
    execution.delete(db)


class TestDigestTaskExecutionCreation:
    """Tests for creating and managing digest task executions."""

    def test_create_basic_digest_execution(
        self,
        db: Session,
        digest_config: DigestConfig,
        digest_execution: DigestTaskExecution,
    ):
        """Test creating a basic digest task execution."""
        digest_execution.update(
            db,
            data={
                "celery_task_id": "test-celery-id",
                "total_recipients": 10,
            },
        )

        assert_default_values(digest_execution)
        assert digest_execution.digest_config_id == digest_config.id
        assert digest_execution.celery_task_id == "test-celery-id"
        assert digest_execution.total_recipients == 10

    def test_create_minimal_digest_execution(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test creating a digest execution with only required fields."""
        execution = DigestTaskExecution.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "action_type": "digest_processing",
                "status": ExecutionLogStatus.pending,
            },
        )

        assert execution.digest_config_id == digest_config.id
        assert execution.celery_task_id is None
        assert execution.total_recipients is None
        assert_default_values(execution)
        execution.delete(db)

    def test_digest_config_id_is_required(self, db: Session):
        """Test that digest_config_id field is required."""
        with pytest.raises(IntegrityError):
            DigestTaskExecution.create(
                db=db,
                data={
                    "action_type": "digest_processing",
                    "celery_task_id": "test-celery-id",
                    "status": ExecutionLogStatus.pending,
                    # Missing digest_config_id
                },
            )

    def test_digest_config_foreign_key_constraint(self, db: Session):
        """Test that digest_config_id must reference a valid digest config."""
        with pytest.raises(IntegrityError):
            DigestTaskExecution.create(
                db=db,
                data={
                    "digest_config_id": "non-existent-id",
                    "action_type": "digest_processing",
                    "status": ExecutionLogStatus.pending,
                },
            )

    def test_create_with_complex_state(
        self,
        db: Session,
        digest_execution: DigestTaskExecution,
    ):
        """Test creating execution with complex execution state and user IDs."""
        complex_state = {
            "current_batch": 2,
            "batch_size": 50,
            "last_processed_timestamp": "2024-01-01T12:00:00Z",
            "processing_metadata": {
                "template_version": "v2.1",
                "filters_applied": ["high_priority", "recent"],
            },
        }
        processed_users = ["user1", "user2", "user3"]

        digest_execution.update(
            db=db,
            data={
                "execution_state": complex_state,
                "processed_user_ids": processed_users,
                "processed_recipients": 3,
                "successful_communications": 2,
                "failed_communications": 1,
            },
        )

        assert digest_execution.execution_state == complex_state
        assert digest_execution.processed_user_ids == processed_users
        assert digest_execution.execution_state["current_batch"] == 2
        assert (
            digest_execution.execution_state["processing_metadata"]["template_version"]
            == "v2.1"
        )


class TestDigestTaskExecutionStatusTransitions:
    """Tests for digest task execution status transition methods."""

    def test_mark_started(self, db: Session, digest_execution: DigestTaskExecution):
        """Test marking execution as started."""
        celery_id = "test-celery-task-id"

        digest_execution.mark_started(db, celery_id)

        assert digest_execution.status == ExecutionLogStatus.in_processing
        assert digest_execution.celery_task_id == celery_id
        assert digest_execution.started_at is not None

    def test_mark_completed(self, db: Session, digest_execution: DigestTaskExecution):
        """Test marking execution as completed."""
        # First start the execution
        digest_execution.mark_started(db, "test-celery-id")

        digest_execution.mark_completed(db)

        assert digest_execution.status == ExecutionLogStatus.complete
        assert digest_execution.completed_at is not None

    def test_mark_failed(self, db: Session, digest_execution: DigestTaskExecution):
        """Test marking execution as failed."""
        error_message = "Email service unavailable"

        digest_execution.mark_failed(db, error_message)

        assert digest_execution.status == ExecutionLogStatus.error
        assert digest_execution.error_message == error_message
        assert digest_execution.completed_at is not None

    def test_status_transition_sequence(
        self, db: Session, digest_execution: DigestTaskExecution
    ):
        """Test a complete status transition sequence."""
        # Start as PENDING
        assert digest_execution.status == ExecutionLogStatus.pending

        # Mark as started
        digest_execution.mark_started(db, "test-celery-id")
        assert digest_execution.status == ExecutionLogStatus.in_processing

        # Mark as completed
        digest_execution.mark_completed(db)
        assert digest_execution.status == ExecutionLogStatus.complete


class TestDigestTaskExecutionProgressTracking:
    """Tests for digest task execution progress tracking functionality."""

    def test_update_progress_basic(
        self, db: Session, digest_execution: DigestTaskExecution
    ):
        """Test basic progress update functionality."""
        processed_users = ["user1", "user2", "user3"]

        digest_execution.update_progress(
            db=db,
            processed_count=3,
            successful_count=2,
            failed_count=1,
            processed_user_ids=processed_users,
        )

        assert digest_execution.processed_recipients == 3
        assert digest_execution.successful_communications == 2
        assert digest_execution.failed_communications == 1
        assert digest_execution.processed_user_ids == processed_users
        assert digest_execution.last_checkpoint_at is not None

    def test_update_progress_with_execution_state(
        self, db: Session, digest_execution: DigestTaskExecution
    ):
        """Test progress update with execution state."""
        processed_users = ["user1", "user2"]
        execution_state = {
            "current_batch": 1,
            "batch_size": 50,
            "last_email_sent_at": "2024-01-01T10:30:00Z",
        }

        digest_execution.update_progress(
            db=db,
            processed_count=2,
            successful_count=2,
            failed_count=0,
            processed_user_ids=processed_users,
            execution_state=execution_state,
        )

        assert digest_execution.processed_recipients == 2
        assert digest_execution.successful_communications == 2
        assert digest_execution.failed_communications == 0
        assert digest_execution.processed_user_ids == processed_users
        assert digest_execution.execution_state == execution_state
        assert digest_execution.execution_state["current_batch"] == 1

    def test_update_progress_without_execution_state(
        self, db: Session, digest_execution: DigestTaskExecution
    ):
        """Test that progress update without execution_state doesn't overwrite existing state."""
        # Set initial state
        initial_state = {"initial": "state"}
        digest_execution.execution_state = initial_state
        digest_execution.save(db)

        # Update progress without execution_state
        digest_execution.update_progress(
            db=db,
            processed_count=1,
            successful_count=1,
            failed_count=0,
            processed_user_ids=["user1"],
        )

        # State should remain unchanged
        assert digest_execution.execution_state == initial_state

    def test_multiple_progress_updates(
        self, db: Session, digest_execution: DigestTaskExecution
    ):
        """Test multiple progress updates accumulate correctly."""
        # First update
        digest_execution.update_progress(
            db=db,
            processed_count=5,
            successful_count=4,
            failed_count=1,
            processed_user_ids=["user1", "user2", "user3", "user4", "user5"],
        )

        # Second update
        digest_execution.update_progress(
            db=db,
            processed_count=10,
            successful_count=8,
            failed_count=2,
            processed_user_ids=[
                "user1",
                "user2",
                "user3",
                "user4",
                "user5",
                "user6",
                "user7",
                "user8",
                "user9",
                "user10",
            ],
        )

        assert digest_execution.processed_recipients == 10
        assert digest_execution.successful_communications == 8
        assert digest_execution.failed_communications == 2
        assert len(digest_execution.processed_user_ids) == 10


class TestDigestTaskExecutionResumption:
    """Tests for digest task execution resumption functionality."""

    def test_can_resume_task(self, db: Session, digest_execution: DigestTaskExecution):
        """Test that in-progress and awaiting processing tasks can be resumed."""
        digest_execution.mark_started(db, "test-celery-id")
        digest_execution.update_progress(
            db=db,
            processed_count=3,
            successful_count=3,
            failed_count=0,
            processed_user_ids=["user1", "user2", "user3"],
        )

        assert digest_execution.can_resume() is True

        digest_execution.mark_awaiting_processing(db)
        assert digest_execution.can_resume() is True

    def test_cannot_resume_completed_task(
        self, db: Session, digest_execution: DigestTaskExecution
    ):
        """Test that completed tasks cannot be resumed."""
        digest_execution.mark_started(db, "test-celery-id")
        digest_execution.mark_completed(db)

        assert digest_execution.can_resume() is False

    def test_cannot_resume_failed_task(
        self, db: Session, digest_execution: DigestTaskExecution
    ):
        """Test that failed tasks cannot be resumed."""
        digest_execution.mark_failed(db, "Test error")

        assert digest_execution.can_resume() is False

    def test_cannot_resume_pending_task(self, digest_execution: DigestTaskExecution):
        """Test that pending tasks cannot be resumed."""
        assert digest_execution.status == ExecutionLogStatus.pending
        assert digest_execution.can_resume() is False

    def test_cannot_resume_without_processed_user_ids(
        self, db: Session, digest_execution: DigestTaskExecution
    ):
        """Test that tasks without processed_user_ids cannot be resumed."""
        digest_execution.mark_started(db, "test-celery-id")
        # Don't set processed_user_ids

        assert digest_execution.can_resume() is False

    def test_get_remaining_work(
        self, db: Session, digest_execution: DigestTaskExecution
    ):
        """Test getting remaining work information."""
        processed_users = ["user1", "user2", "user3"]
        execution_state = {
            "current_batch": 1,
            "last_processed_timestamp": "2024-01-01T10:00:00Z",
        }

        digest_execution.update_progress(
            db=db,
            processed_count=3,
            successful_count=2,
            failed_count=1,
            processed_user_ids=processed_users,
            execution_state=execution_state,
        )

        remaining_work = digest_execution.get_remaining_work()

        assert remaining_work["processed_user_ids"] == processed_users
        assert remaining_work["execution_state"] == execution_state
        assert remaining_work["processed_count"] == 3
        assert remaining_work["successful_count"] == 2
        assert remaining_work["failed_count"] == 1

    def test_get_remaining_work_with_defaults(
        self, digest_execution: DigestTaskExecution
    ):
        """Test getting remaining work with default values."""
        remaining_work = digest_execution.get_remaining_work()

        assert remaining_work["processed_user_ids"] == []
        assert remaining_work["execution_state"] == {}
        assert remaining_work["processed_count"] == 0
        assert remaining_work["successful_count"] == 0
        assert remaining_work["failed_count"] == 0


class TestDigestTaskExecutionRelationships:
    """Tests for digest task execution relationships."""

    def test_digest_config_relationship(
        self,
        db: Session,
        digest_config: DigestConfig,
        digest_execution: DigestTaskExecution,
    ):
        """Test relationship with digest config."""

        # Test forward relationship
        assert digest_execution.digest_config == digest_config
        assert digest_execution.digest_config.id == digest_config.id

        # Test backward relationship
        assert digest_execution in digest_config.executions

        digest_execution.delete(db)

    def test_cascade_delete_from_digest_config(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that executions are deleted when digest config is deleted."""
        executions = []
        for _ in range(2):
            execution = DigestTaskExecution.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "action_type": "digest_processing",
                    "status": ExecutionLogStatus.pending,
                },
            )
            executions.append(execution)

        # Delete the digest config
        digest_config.delete(db)

        # Verify executions are also deleted
        for execution in executions:
            assert (
                db.query(DigestTaskExecution)
                .filter(DigestTaskExecution.id == execution.id)
                .first()
                is None
            )

    def test_multiple_executions_per_config(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that a digest config can have multiple executions."""
        executions = []
        for i in range(3):
            execution = DigestTaskExecution.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "action_type": "digest_processing",
                    "celery_task_id": f"celery-task-{i}",
                    "status": ExecutionLogStatus.pending,
                },
            )
            executions.append(execution)

        # Refresh the digest config to get updated relationships
        db.refresh(digest_config)

        assert len(digest_config.executions) == 3
        assert all(exec in digest_config.executions for exec in executions)

        # Clean up
        for execution in executions:
            execution.delete(db)


class TestDigestTaskExecutionWorkerTaskInheritance:
    """Tests for WorkerTask inheritance functionality."""

    def test_allowed_action_types(self):
        """Test that allowed action types are correctly defined."""
        allowed_types = DigestTaskExecution.allowed_action_types()
        assert allowed_types == ["digest_processing"]

    def test_invalid_action_type_rejected(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that invalid action types are rejected."""
        with pytest.raises(
            ValueError,
            match="Invalid action_type 'invalid_action' for DigestTaskExecution",
        ):
            DigestTaskExecution.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "action_type": "invalid_action",
                    "status": ExecutionLogStatus.pending,
                },
            )

    def test_inherits_worker_task_fields(self, digest_execution: DigestTaskExecution):
        """Test that DigestTaskExecution inherits WorkerTask fields."""

        # Test WorkerTask inherited fields
        assert hasattr(digest_execution, "id")
        assert hasattr(digest_execution, "created_at")
        assert hasattr(digest_execution, "updated_at")
        assert hasattr(digest_execution, "celery_task_id")

        # Test that it has the digest-specific fields too
        assert hasattr(digest_execution, "digest_config_id")
        assert hasattr(digest_execution, "total_recipients")
        assert hasattr(digest_execution, "processed_recipients")
        assert hasattr(digest_execution, "execution_state")

    def test_tablename_is_correct(self):
        """Test that the table name is correctly set."""
        assert DigestTaskExecution.__tablename__ == "digest_task_execution"


class TestDigestTaskExecutionQueries:
    """Tests for querying digest task executions."""

    @pytest.fixture
    def sample_executions(self, db: Session, digest_config: DigestConfig):
        """Create sample digest executions for testing."""
        executions = []

        # Pending execution
        exec1 = DigestTaskExecution.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "action_type": "digest_processing",
                "status": ExecutionLogStatus.pending,
                "total_recipients": 10,
            },
        )
        executions.append(exec1)

        # In progress execution
        exec2 = DigestTaskExecution.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "action_type": "digest_processing",
                "status": ExecutionLogStatus.in_processing,
                "celery_task_id": "in-progress-task",
                "total_recipients": 20,
                "processed_recipients": 5,
            },
        )
        executions.append(exec2)

        # Completed execution
        exec3 = DigestTaskExecution.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "action_type": "digest_processing",
                "status": ExecutionLogStatus.complete,
                "celery_task_id": "completed-task",
                "total_recipients": 15,
                "processed_recipients": 15,
                "successful_communications": 14,
                "failed_communications": 1,
            },
        )
        executions.append(exec3)

        # Failed execution
        exec4 = DigestTaskExecution.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "action_type": "digest_processing",
                "status": ExecutionLogStatus.error,
                "celery_task_id": "failed-task",
                "error_message": "Service unavailable",
            },
        )
        executions.append(exec4)

        yield executions
        for execution in executions:
            execution.delete(db)

    @pytest.mark.usefixtures("sample_executions")
    def test_filter_by_status(self, db: Session):
        """Test filtering executions by status."""
        pending_executions = (
            db.query(DigestTaskExecution)
            .filter(DigestTaskExecution.status == ExecutionLogStatus.pending)
            .all()
        )
        assert len(pending_executions) == 1
        assert pending_executions[0].status == ExecutionLogStatus.pending

        completed_executions = (
            db.query(DigestTaskExecution)
            .filter(DigestTaskExecution.status == ExecutionLogStatus.complete)
            .all()
        )
        assert len(completed_executions) == 1
        assert completed_executions[0].status == ExecutionLogStatus.complete

    @pytest.mark.usefixtures("sample_executions")
    def test_filter_by_digest_config(self, db: Session, digest_config: DigestConfig):
        """Test filtering executions by digest config."""
        config_executions = (
            db.query(DigestTaskExecution)
            .filter(DigestTaskExecution.digest_config_id == digest_config.id)
            .all()
        )
        assert len(config_executions) == 4
        assert all(
            exec.digest_config_id == digest_config.id for exec in config_executions
        )

    @pytest.mark.usefixtures("sample_executions")
    def test_filter_by_celery_task_id(self, db: Session):
        """Test filtering executions by celery task ID."""
        execution = (
            db.query(DigestTaskExecution)
            .filter(DigestTaskExecution.celery_task_id == "in-progress-task")
            .first()
        )
        assert execution is not None
        assert execution.celery_task_id == "in-progress-task"
        assert execution.status == ExecutionLogStatus.in_processing

    @pytest.mark.usefixtures("sample_executions")
    def test_filter_resumable_executions(self, db: Session):
        """Test filtering executions that can be resumed."""
        # First, set up some executions that can be resumed
        resumable_exec = (
            db.query(DigestTaskExecution)
            .filter(DigestTaskExecution.status == ExecutionLogStatus.in_processing)
            .first()
        )
        # Add processed_user_ids to make it resumable
        resumable_exec.processed_user_ids = ["user1", "user2"]
        resumable_exec.save(db)

        # Query for resumable executions
        resumable_executions = [
            exec for exec in db.query(DigestTaskExecution).all() if exec.can_resume()
        ]

        assert len(resumable_executions) == 1
        assert resumable_executions[0].status == ExecutionLogStatus.in_processing


class TestDigestTaskExecutionValidation:
    """Tests for digest task execution validation and constraints."""

    def test_valid_status_values(self, db: Session, digest_config: DigestConfig):
        """Test that all valid status values can be set."""
        for status in ExecutionLogStatus:
            execution = DigestTaskExecution.create(
                db=db,
                data={
                    "digest_config_id": digest_config.id,
                    "action_type": "digest_processing",
                    "status": status,
                },
            )
            assert execution.status.value == status.value
            execution.delete(db)

    def test_complex_execution_state_storage(
        self, db: Session, digest_config: DigestConfig
    ):
        """Test that complex execution state structures are properly stored."""
        complex_state = {
            "batches": [
                {"batch_id": 1, "size": 50, "status": "completed"},
                {"batch_id": 2, "size": 30, "status": "in_progress"},
            ],
            "metadata": {
                "template_id": "weekly_digest_v2",
                "filters": {
                    "date_range": {"start": "2024-01-01", "end": "2024-01-07"},
                    "priority": ["high", "medium"],
                },
                "recipients": {
                    "total": 100,
                    "by_department": {"legal": 30, "compliance": 40, "admin": 30},
                },
            },
            "timestamps": {
                "batch_1_started": "2024-01-01T09:00:00Z",
                "batch_1_completed": "2024-01-01T09:15:00Z",
                "batch_2_started": "2024-01-01T09:15:00Z",
            },
        }

        execution = DigestTaskExecution.create(
            db=db,
            data={
                "digest_config_id": digest_config.id,
                "action_type": "digest_processing",
                "status": ExecutionLogStatus.pending,
                "execution_state": complex_state,
            },
        )

        db.refresh(execution)

        assert execution.execution_state == complex_state
        assert execution.execution_state["batches"][0]["batch_id"] == 1
        assert (
            execution.execution_state["metadata"]["template_id"] == "weekly_digest_v2"
        )
        assert (
            execution.execution_state["metadata"]["recipients"]["by_department"][
                "legal"
            ]
            == 30
        )
        execution.delete(db)
