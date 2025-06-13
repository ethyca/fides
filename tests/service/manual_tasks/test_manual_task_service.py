import pytest
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
)
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskParentEntityType,
    ManualTaskReferenceType,
    ManualTaskType,
)
from fides.service.manual_tasks.manual_task_service import ManualTaskService
from tests.service.manual_tasks.conftest import (
    ATTACHMENT_FIELD_KEY,
    CHECKBOX_FIELD_KEY,
    FIELDS,
    TEXT_FIELD_KEY,
)


@pytest.fixture
def manual_task(db: Session):
    task = ManualTask.create(
        db=db,
        data={
            "parent_entity_id": "test-parent-id",
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
            "task_type": ManualTaskType.privacy_request,
        },
    )

    ManualTaskReference.create(
        db=db,
        data={
            "task_id": task.id,
            "reference_id": task.parent_entity_id,
            "reference_type": ManualTaskReferenceType.connection_config,
        },
    )

    yield task
    task.delete(db)


@pytest.fixture
def respondent_user(db: Session):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_respondent_user",
            "email_address": "fides.user@ethyca.com",
        },
    )
    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [RESPONDENT]})
    yield user
    user.delete(db)


@pytest.fixture
def external_user(db: Session):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_external_user",
            "email_address": "user@not_ethyca.com",
        },
    )
    FidesUserPermissions.create(
        db=db, data={"user_id": user.id, "roles": [EXTERNAL_RESPONDENT]}
    )
    yield user
    user.delete(db)


@pytest.fixture
def manual_task_service(db: Session):
    return ManualTaskService(db)


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
        respondent_user: FidesUser,
    ):
        # Setup
        user_ids = ["user1", "user2", respondent_user.id]

        # Execute
        manual_task_service.assign_users_to_task(
            task_id=manual_task.id, user_ids=user_ids
        )

        # Verify
        db.refresh(manual_task)
        assert (
            len(manual_task.references) == 2
        )  # The parent entity, and respondent user
        assert any(
            ref.reference_id == respondent_user.id for ref in manual_task.references
        )
        assert all(
            ref.reference_id not in ["user1", "user2"] for ref in manual_task.references
        )

        # Verify logs were created
        logs = (
            db.query(ManualTaskLog)
            .filter(ManualTaskLog.task_id == manual_task.id)
            .all()
        )

        # Verify error log for non-existent users
        error_log = next(log for log in logs if log.status == ManualTaskLogStatus.error)
        assert (
            error_log.message
            == "Error in Verify user IDs: User(s) ['user1', 'user2'] do not exist"
        )

        # Verify success log for assigned user
        success_log = next(
            log for log in logs if log.status == ManualTaskLogStatus.complete
        )
        assert success_log.message == "Assign users to task"
        assert success_log.details == {"assigned_users": [respondent_user.id]}

        # Verify the successful assignment happened
        assert (
            len(manual_task.references) == 2
        )  # The parent entity, and respondent user
        assert any(
            ref.reference_id == respondent_user.id for ref in manual_task.references
        )
        assert all(
            ref.reference_id not in ["user1", "user2"] for ref in manual_task.references
        )

    def test_assign_users_to_task_success(
        self,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
        external_user: FidesUser,
    ):
        # Execute
        manual_task_service.assign_users_to_task(
            task_id=manual_task.id, user_ids=[respondent_user.id, external_user.id]
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
        assert any(log.message == "Assign users to task" for log in manual_task.logs)
        assign_log = next(
            log for log in manual_task.logs if log.message == "Assign users to task"
        )
        assert assign_log.details == {
            "assigned_users": sorted([respondent_user.id, external_user.id])
        }

    def test_assign_users_to_task_empty_list(
        self,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        with pytest.raises(ValueError, match="User ID is required for assignment"):
            manual_task_service.assign_users_to_task(
                task_id=manual_task.id, user_ids=[]
            )

    def test_assign_users_to_task_duplicate_users(
        self,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
    ):
        # Execute
        manual_task_service.assign_users_to_task(
            task_id=manual_task.id, user_ids=[respondent_user.id, respondent_user.id]
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
        assert any(log.message == "Assign users to task" for log in manual_task.logs)
        assign_log = next(
            log for log in manual_task.logs if log.message == "Assign users to task"
        )
        assert assign_log.details == {"assigned_users": [respondent_user.id]}

    def test_assign_users_to_task_already_assigned(
        self,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
    ):
        # Setup - assign user first time
        manual_task_service.assign_users_to_task(
            task_id=manual_task.id, user_ids=[respondent_user.id]
        )
        initial_reference_count = len(manual_task.references)
        initial_log_count = len(manual_task.logs)

        # Execute - assign same user again
        manual_task_service.assign_users_to_task(
            task_id=manual_task.id, user_ids=[respondent_user.id]
        )

        # Verify - no new references or logs should be created
        assert len(manual_task.references) == initial_reference_count
        assert any(log.message == "Assign users to task" for log in manual_task.logs)
        assign_log = next(
            log for log in manual_task.logs if log.message == "Assign users to task"
        )
        assert assign_log.details == {"assigned_users": [respondent_user.id]}


class TestUnassignUsersFromTask:
    """Tests for the unassign_users_from_task method."""

    def test_unassign_users_from_task(
        self,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
        external_user: FidesUser,
    ):
        # Setup
        manual_task_service.assign_users_to_task(
            task_id=manual_task.id, user_ids=[respondent_user.id, external_user.id]
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
            task_id=manual_task.id, user_ids=[respondent_user.id, external_user.id]
        )

        # Verify
        assert len(manual_task.references) == 1  # The parent entity
        verify_expected_reference_ids(manual_task, [manual_task.parent_entity_id])
        verify_expected_reference_types(
            manual_task, [ManualTaskReferenceType.connection_config]
        )

        # Verify logs were created
        assert any(log.message == "Assign users to task" for log in manual_task.logs)
        assign_log = next(
            log for log in manual_task.logs if log.message == "Assign users to task"
        )
        assert assign_log.details == {
            "assigned_users": sorted([respondent_user.id, external_user.id])
        }
        assert any(
            log.message == "Unassign users from task" for log in manual_task.logs
        )
        unassign_log = next(
            log for log in manual_task.logs if log.message == "Unassign users from task"
        )
        assert unassign_log.details == {
            "unassigned_users": sorted([respondent_user.id, external_user.id])
        }

    def test_unassign_users_from_task_partial(
        self,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
        external_user: FidesUser,
    ):
        # Setup
        assign_user_ids = [respondent_user.id, external_user.id]
        unassign_user_ids = [respondent_user.id, "user3"]

        manual_task_service.assign_users_to_task(
            task_id=manual_task.id, user_ids=assign_user_ids
        )
        # Execute
        manual_task_service.unassign_users_from_task(
            task_id=manual_task.id, user_ids=unassign_user_ids
        )

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
        assert any(log.message == "Assign users to task" for log in manual_task.logs)
        assign_log = next(
            log for log in manual_task.logs if log.message == "Assign users to task"
        )
        assert assign_log.details == {
            "assigned_users": sorted([respondent_user.id, external_user.id])
        }
        assert any(
            log.message == "Unassign users from task" for log in manual_task.logs
        )
        unassign_log = next(
            log for log in manual_task.logs if log.message == "Unassign users from task"
        )
        assert unassign_log.details == {"unassigned_users": [respondent_user.id]}

    def test_unassign_users_from_task_empty_list(
        self,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        # Execute
        with pytest.raises(ValueError, match="User ID is required for unassignment"):
            manual_task_service.unassign_users_from_task(
                task_id=manual_task.id, user_ids=[]
            )

    def test_unassign_users_from_task_duplicate_users(
        self,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
    ):
        # Setup
        manual_task_service.assign_users_to_task(
            task_id=manual_task.id, user_ids=[respondent_user.id]
        )

        # Execute
        manual_task_service.unassign_users_from_task(
            task_id=manual_task.id, user_ids=[respondent_user.id, respondent_user.id]
        )

        # Verify
        assert len(manual_task.references) == 1  # Only the parent entity
        # All log messages:
        # Message: 'Created manual task for privacy_request', Status: created
        # Message: 'Assign users to task', Status: complete
        # Message: 'Unassign users from task', Status: complete
        assign_log = next(
            log for log in manual_task.logs if log.message == "Assign users to task"
        )
        assert assign_log.details == {"assigned_users": [respondent_user.id]}
        unassign_log = next(
            log for log in manual_task.logs if log.message == "Unassign users from task"
        )
        assert unassign_log.details == {"unassigned_users": [respondent_user.id]}


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
            task_id=manual_task.id,
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
        text_field = next(
            field
            for field in config.field_definitions
            if field.field_key == TEXT_FIELD_KEY
        )
        checkbox_field = next(
            field
            for field in config.field_definitions
            if field.field_key == CHECKBOX_FIELD_KEY
        )
        attachment_field = next(
            field
            for field in config.field_definitions
            if field.field_key == ATTACHMENT_FIELD_KEY
        )
        assert (
            text_field.field_metadata["label"] == FIELDS[0]["field_metadata"]["label"]
        )
        assert (
            checkbox_field.field_metadata["label"]
            == FIELDS[1]["field_metadata"]["label"]
        )
        assert (
            attachment_field.field_metadata["label"]
            == FIELDS[2]["field_metadata"]["label"]
        )

        # Verify log was created
        log = (
            db.query(ManualTaskLog)
            .filter_by(task_id=manual_task.id)
            .order_by(ManualTaskLog.created_at.desc())
            .first()
        )
        assert log is not None
        assert log.status == ManualTaskLogStatus.complete
        assert f"Creating new configuration version" in log.message
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
            config_type=ManualTaskConfigurationType.access_privacy_request,
            fields=FIELDS,
            task_id=manual_task.id,
        )
        db.commit()  # Commit the create transaction
        db.refresh(manual_task)

        config = manual_task_service.config_service.get_current_config(
            task=manual_task,
            config_type=ManualTaskConfigurationType.access_privacy_request,
        )
        assert config is not None

        # Verify task exists
        task = manual_task_service.get_task(task_id=manual_task.id)
        assert task is not None

        # Execute
        manual_task_service.delete_config(config=config, task_id=manual_task.id)
        db.commit()  # Commit the delete transaction

        # Verify
        db.refresh(manual_task)
        assert db.query(ManualTaskConfig).filter_by(id=config.id).first() is None

        # Verify logs were created
        logs = (
            db.query(ManualTaskLog)
            .filter_by(task_id=manual_task.id)
            .order_by(ManualTaskLog.created_at.desc())
            .all()
        )

        # We expect logs from both service layers:
        # From ManualTaskConfigService:
        # 1. "Creating new configuration version"
        # 2. "Deleting Manual Task configuration"
        # Plus initial task creation:
        # 3. "Created manual task configuration for access_privacy_request"
        # 5. "Created manual task for privacy_request"
        assert len(logs) == 4

        # Verify the most recent logs first (delete operations)
        delete_logs = logs[:1]  # The two most recent logs

        # Verify delete logs
        assert any(
            log.message == "Deleting Manual Task configuration"
            and log.status == ManualTaskLogStatus.complete
            for log in delete_logs
        )

        # Verify create logs
        create_logs = [log for log in logs if "config" in log.message.lower()]
        assert any(
            log.message
            == "Created manual task configuration for access_privacy_request"
            and log.status == ManualTaskLogStatus.created
            for log in create_logs
        )
        assert any(
            log.message == "Creating new configuration version"
            and log.status == ManualTaskLogStatus.complete
            for log in create_logs
        )

        # Verify all logs have the correct task_id and no instance_id
        for log in logs:
            assert log.task_id == manual_task.id
            assert log.instance_id is None  # Ensure no instance_id is set
