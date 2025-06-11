import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.manual_tasks.manual_task import ManualTask, ManualTaskReference
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.manual_tasks.manual_task_log import (
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.oauth.roles import EXTERNAL_RESPONDENT, RESPONDENT
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskTextField,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskParentEntityType,
    ManualTaskReferenceType,
    ManualTaskType,
)
from fides.service.manual_tasks.manual_task_service import ManualTaskService
from tests.service.manual_tasks.conftest import FIELDS

# Helper functions


def verify_expected_reference_types(
    manual_task: ManualTask, expected_reference_types: list[ManualTaskReferenceType]
):
    assert all(
        ref.reference_type in expected_reference_types for ref in manual_task.references
    )


def verify_expected_reference_ids(
    manual_task: ManualTask, expected_reference_ids: list[str]
):
    assert all(
        ref.reference_id in expected_reference_ids for ref in manual_task.references
    )


def verify_expected_logs(logs: list[ManualTaskLog], expected_messages: list[str]):
    assert len(logs) == len(expected_messages)
    assert all(log.message in expected_messages for log in logs)


class TestGetTask:
    """Tests for the get_task method."""

    def test_get_task_by_id(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        assert manual_task_service.get_task(task_id=manual_task.id) == manual_task

    def test_get_task_by_parent_entity(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        assert (
            manual_task_service.get_task(
                parent_entity_id="test-parent-id",
                parent_entity_type=ManualTaskParentEntityType.connection_config,
            )
            == manual_task
        )

    def test_get_task_by_type(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        assert (
            manual_task_service.get_task(task_type=ManualTaskType.privacy_request)
            == manual_task
        )

    def test_get_task_no_filters(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        assert manual_task_service.get_task() is None

    def test_get_task_invalid_id(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        assert manual_task_service.get_task(task_id="invalid-id") is None

    def test_get_task_invalid_parent_entity_type(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        assert (
            manual_task_service.get_task(
                parent_entity_id="test-parent-id",
                parent_entity_type="invalid_type",
            )
            is None
        )

    def test_get_task_invalid_task_type(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        assert manual_task_service.get_task(task_type="invalid_type") is None


class TestAssignUsersToTask:
    """Tests for the assign_users_to_task method."""

    def test_assign_users_to_task_error_user_not_found(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        # Setup
        user_ids = ["user1", "user2"]
        manual_task_service.assign_users_to_task(db, manual_task, user_ids)

        # Verify
        assert len(manual_task.references) == 1  # The parent entity
        assert all(ref.reference_id not in user_ids for ref in manual_task.references)

        # Verify logs were created
        # There should be at least 2 logs, one for each user
        assert len(manual_task.logs) >= 2

        # Get error logs
        error_logs = [
            log for log in manual_task.logs if log.status == ManualTaskLogStatus.error
        ]
        assert len(error_logs) == 2
        for log in error_logs:
            assert (
                log.message
                == f"Failed to add user {log.details['user_id']} to task {manual_task.id}: user does not exist"
            )

    def test_assign_users_to_task_success(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
        external_user: FidesUser,
    ):
        # Execute
        manual_task_service.assign_users_to_task(
            db, manual_task, [respondent_user.id, external_user.id]
        )

        # Verify
        assert len(manual_task.references) == 3  # The parent entity + the two users
        verify_expected_reference_ids(
            manual_task,
            [manual_task.parent_entity_id, respondent_user.id, external_user.id],
        )
        verify_expected_reference_types(
            manual_task,
            [
                ManualTaskReferenceType.connection_config,
                ManualTaskReferenceType.assigned_user,
            ],
        )

        # Verify logs were created
        assert (
            len(manual_task.logs) == 3
        )  # Create task and update tasks for the two users

    def test_assign_users_to_task_empty_list(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        with pytest.raises(ValueError, match="User ID is required for assignment"):
            manual_task_service.assign_users_to_task(db, manual_task, [])

    def test_assign_users_to_task_duplicate_users(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
    ):
        # Execute
        manual_task_service.assign_users_to_task(
            db, manual_task, [respondent_user.id, respondent_user.id]
        )

        # Verify
        assert (
            len(manual_task.references) == 2
        )  # The parent entity + one user (duplicate ignored)
        assert all(
            ref.reference_id == respondent_user.id
            for ref in manual_task.references
            if ref.reference_type == ManualTaskReferenceType.assigned_user
        )

        # Verify logs were created
        assert len(manual_task.logs) == 2  # Create task and one update task

    def test_assign_users_to_task_already_assigned(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
    ):
        # Setup - assign user first time
        manual_task_service.assign_users_to_task(db, manual_task, [respondent_user.id])
        initial_reference_count = len(manual_task.references)
        initial_log_count = len(manual_task.logs)

        # Execute - assign same user again
        manual_task_service.assign_users_to_task(db, manual_task, [respondent_user.id])

        # Verify - no new references or logs should be created
        assert len(manual_task.references) == initial_reference_count
        assert len(manual_task.logs) == initial_log_count


class TestUnassignUsersFromTask:
    """Tests for the unassign_users_from_task method."""

    def test_unassign_users_from_task(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
        external_user: FidesUser,
    ):
        # Setup
        manual_task_service.assign_users_to_task(
            db, manual_task, [respondent_user.id, external_user.id]
        )

        # Verify
        assert len(manual_task.references) == 3  # The parent entity + the two users
        verify_expected_reference_ids(
            manual_task,
            [manual_task.parent_entity_id, respondent_user.id, external_user.id],
        )
        verify_expected_reference_types(
            manual_task,
            [
                ManualTaskReferenceType.connection_config,
                ManualTaskReferenceType.assigned_user,
            ],
        )

        # Execute
        manual_task_service.unassign_users_from_task(
            db, manual_task, [respondent_user.id, external_user.id]
        )

        # Verify
        assert len(manual_task.references) == 1  # The parent entity
        verify_expected_reference_ids(manual_task, [manual_task.parent_entity_id])
        verify_expected_reference_types(
            manual_task, [ManualTaskReferenceType.connection_config]
        )

        # Verify logs were created
        assert (
            len(manual_task.logs) == 5
        )  # Create task and update tasks for the two users assign and unassign
        update_logs = [
            log for log in manual_task.logs if log.status == ManualTaskLogStatus.updated
        ]
        assert len(update_logs) == 4
        verify_expected_logs(
            update_logs,
            [
                f"User {respondent_user.id} unassigned from task",
                f"User {external_user.id} unassigned from task",
                f"User {respondent_user.id} assigned to task",
                f"User {external_user.id} assigned to task",
            ],
        )

    def test_unassign_users_from_task_partial(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
        external_user: FidesUser,
    ):
        # Setup
        assign_user_ids = [respondent_user.id, external_user.id]
        unassign_user_ids = [respondent_user.id, "user3"]

        manual_task_service.assign_users_to_task(db, manual_task, assign_user_ids)
        # Execute
        manual_task_service.unassign_users_from_task(db, manual_task, unassign_user_ids)

        # Verify
        assert len(manual_task.references) == 2  # The parent entity and external user
        verify_expected_reference_ids(
            manual_task, [manual_task.parent_entity_id, external_user.id]
        )
        verify_expected_reference_types(
            manual_task,
            [
                ManualTaskReferenceType.connection_config,
                ManualTaskReferenceType.assigned_user,
            ],
        )

        # Verify logs were created
        assert (
            len(manual_task.logs) == 4
        )  # Create task and update tasks for the two users (assigned) and one user unassigned

        update_logs = [
            log for log in manual_task.logs if log.status == ManualTaskLogStatus.updated
        ]
        verify_expected_logs(
            update_logs,
            [
                f"User {respondent_user.id} unassigned from task",
                f"User {respondent_user.id} assigned to task",
                f"User {external_user.id} assigned to task",
            ],
        )

    def test_unassign_users_from_task_empty_list(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        # Execute
        with pytest.raises(ValueError, match="User ID is required for unassignment"):
            manual_task_service.unassign_users_from_task(db, manual_task, [])

    def test_unassign_users_from_task_duplicate_users(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
    ):
        # Setup
        manual_task_service.assign_users_to_task(db, manual_task, [respondent_user.id])

        # Execute
        manual_task_service.unassign_users_from_task(
            db, manual_task, [respondent_user.id, respondent_user.id]
        )

        # Verify
        assert len(manual_task.references) == 1  # Only the parent entity
        assert (
            len(manual_task.logs) == 3
        )  # Create task and two update tasks (assign and unassign)


class TestManualTaskConfig:
    """Tests for the config-related methods."""

    def test_create_config(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        """Test creating a new config for a task."""
        # Execute
        manual_task_service.create_config(
            task=manual_task,
            config_type=ManualTaskConfigurationType.access_privacy_request,
            fields=FIELDS,
        )

        # Verify
        config = manual_task_service.config_service.get_current_config(
            task=manual_task,
            config_type=ManualTaskConfigurationType.access_privacy_request,
        )
        assert config is not None
        assert config.config_type == ManualTaskConfigurationType.access_privacy_request
        assert config.version == 1
        assert config.is_current is True
        assert len(config.field_definitions) == len(FIELDS)
        field1 = next(
            field for field in config.field_definitions if field.field_key == "field1"
        )
        field2 = next(
            field for field in config.field_definitions if field.field_key == "field2"
        )
        assert field1.field_metadata["label"] == FIELDS[0]["field_metadata"]["label"]
        assert field2.field_metadata["label"] == FIELDS[1]["field_metadata"]["label"]

        # Verify log was created
        log = (
            db.query(ManualTaskLog)
            .filter_by(task_id=manual_task.id)
            .order_by(ManualTaskLog.created_at.desc())
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.created
        assert "Created new version 1 of configuration" in log.message
        assert log.config_id == config.id

    def test_delete_config(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        """Test deleting a config for a task."""
        # Setup - create config
        manual_task_service.create_config(
            task=manual_task,
            config_type=ManualTaskConfigurationType.access_privacy_request,
            fields=FIELDS,
        )
        config = manual_task_service.config_service.get_current_config(
            task=manual_task,
            config_type=ManualTaskConfigurationType.access_privacy_request,
        )
        assert config is not None

        # Execute
        manual_task_service.delete_config(manual_task, config)

        # Verify
        assert db.query(ManualTaskConfig).filter_by(id=config.id).first() is None

        # Verify log was created
        log = (
            db.query(ManualTaskLog)
            .filter_by(task_id=manual_task.id)
            .order_by(ManualTaskLog.created_at.desc())
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.complete
        assert (
            f"Deleted manual task configuration for {config.config_type}" in log.message
        )
