import pytest
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.manual_tasks.manual_task import ManualTask, ManualTaskReference
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
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

    @pytest.mark.parametrize(
        "search_params,expected_error",
        [
            pytest.param(
                {"task_id": "test-task-id"},
                None,
                id="task_id",
            ),
            pytest.param(
                {
                    "parent_entity_id": "test-parent-id",
                    "parent_entity_type": ManualTaskParentEntityType.connection_config,
                },
                None,
                id="parent_entity_id",
            ),
            pytest.param(
                {"task_type": ManualTaskType.privacy_request},
                None,
                id="task_type",
            ),
            pytest.param(
                {},
                "No filters provided to get_task",
                id="no_filters",
            ),
            pytest.param(
                {"task_id": "invalid-id"},
                r"No task found with filters: \['task_id=invalid-id'\]",
                id="invalid_task_id",
            ),
            pytest.param(
                {
                    "parent_entity_id": "test-parent-id",
                    "parent_entity_type": "invalid_type",
                },
                r"No task found with filters: \['parent_entity_id=test-parent-id', 'parent_entity_type=invalid_type'\]",
                id="invalid_parent_entity_type",
            ),
            pytest.param(
                {"task_type": "invalid_type"},
                r"No task found with filters: \['task_type=invalid_type'\]",
                id="invalid_task_type",
            ),
        ],
    )
    def test_get_task(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        search_params: dict,
        expected_error: str,
    ):
        """Test getting tasks with various search parameters."""
        if "task_id" in search_params and search_params["task_id"] == "test-task-id":
            search_params["task_id"] = manual_task.id

        if expected_error:
            with pytest.raises(ValueError, match=expected_error):
                manual_task_service.get_task(**search_params)
        else:
            result = manual_task_service.get_task(**search_params)
            assert result == manual_task


class TestAssignUsersToTask:
    """Tests for the assign_users_to_task method."""

    @pytest.mark.parametrize(
        "user_ids,expected_assigned,expected_not_assigned,should_raise",
        [
            pytest.param(
                ["user1", "user2", "respondent_user"],  # user_ids
                ["respondent_user"],  # expected_assigned
                ["user1", "user2"],  # expected_not_assigned
                False,  # should_raise
                id="user_ids",
            ),
            pytest.param(
                ["respondent_user", "external_user"],  # user_ids
                ["respondent_user", "external_user"],  # expected_assigned
                [],  # expected_not_assigned
                False,  # should_raise
                id="respondent_user_external_user",
            ),
            pytest.param(
                [],  # user_ids
                [],  # expected_assigned
                [],  # expected_not_assigned
                True,  # should_raise
                id="empty_user_ids",
            ),
            pytest.param(
                ["respondent_user", "respondent_user"],  # user_ids
                ["respondent_user"],  # expected_assigned
                [],  # expected_not_assigned
                False,  # should_raise
                id="respondent_user_duplicate",
            ),
        ],
    )
    def test_assign_users_to_task(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
        external_user: FidesUser,
        user_ids: list[str],
        expected_assigned: list[str],
        expected_not_assigned: list[str],
        should_raise: bool,
    ):
        """Test assigning users to tasks with various scenarios."""
        # Replace placeholder user IDs with actual IDs
        user_ids = [
            (
                respondent_user.id
                if id == "respondent_user"
                else external_user.id if id == "external_user" else id
            )
            for id in user_ids
        ]
        expected_assigned = [
            (
                respondent_user.id
                if id == "respondent_user"
                else external_user.id if id == "external_user" else id
            )
            for id in expected_assigned
        ]

        if should_raise:
            with pytest.raises(ValueError, match="User ID is required for assignment"):
                manual_task_service.assign_users_to_task(
                    task_id=manual_task.id, user_ids=user_ids
                )
            return

        # Execute
        manual_task_service.assign_users_to_task(
            task_id=manual_task.id, user_ids=user_ids
        )

        # Verify references
        expected_ref_count = 1 + len(
            expected_assigned
        )  # parent entity + assigned users
        assert len(manual_task.references) == expected_ref_count

        verify_expected_reference_ids(
            manual_task,
            [manual_task.parent_entity_id] + expected_assigned,
        )
        verify_expected_reference_types(
            manual_task,
            [
                ManualTaskReferenceType.connection_config,
                ManualTaskReferenceType.assigned_user,
            ],
        )

        # Verify logs
        assign_log = next(
            log for log in manual_task.logs if log.message == "Assign users to task"
        )
        assert assign_log.details["assigned_users"] == sorted(expected_assigned)
        if expected_not_assigned:
            assert sorted(assign_log.details["user_ids_not_assigned"]) == sorted(
                expected_not_assigned
            )


class TestUnassignUsersFromTask:
    """Tests for the unassign_users_from_task method."""

    @pytest.mark.parametrize(
        "initial_users,unassign_users,expected_remaining,expected_not_unassigned,should_raise",
        [
            (
                ["respondent_user", "external_user"],  # initial_users
                ["respondent_user", "external_user"],  # unassign_users
                [],  # expected_remaining
                [],  # expected_not_unassigned
                False,  # should_raise
            ),
            (
                ["respondent_user", "external_user"],  # initial_users
                ["respondent_user", "user3"],  # unassign_users
                ["external_user"],  # expected_remaining
                ["user3"],  # expected_not_unassigned
                False,  # should_raise
            ),
            (
                [],  # initial_users
                [],  # unassign_users
                [],  # expected_remaining
                [],  # expected_not_unassigned
                True,  # should_raise
            ),
            (
                ["respondent_user"],  # initial_users
                ["respondent_user", "respondent_user"],  # unassign_users
                [],  # expected_remaining
                [],  # expected_not_unassigned
                False,  # should_raise
            ),
        ],
    )
    def test_unassign_users_from_task(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
        respondent_user: FidesUser,
        external_user: FidesUser,
        initial_users: list[str],
        unassign_users: list[str],
        expected_remaining: list[str],
        expected_not_unassigned: list[str],
        should_raise: bool,
    ):
        """Test unassigning users from tasks with various scenarios."""
        # Replace placeholder user IDs with actual IDs
        initial_users = [
            (
                respondent_user.id
                if id == "respondent_user"
                else external_user.id if id == "external_user" else id
            )
            for id in initial_users
        ]
        unassign_users = [
            (
                respondent_user.id
                if id == "respondent_user"
                else external_user.id if id == "external_user" else id
            )
            for id in unassign_users
        ]
        expected_remaining = [
            (
                respondent_user.id
                if id == "respondent_user"
                else external_user.id if id == "external_user" else id
            )
            for id in expected_remaining
        ]

        # Setup - assign initial users
        if initial_users:
            manual_task_service.assign_users_to_task(
                task_id=manual_task.id, user_ids=initial_users
            )

        if should_raise:
            with pytest.raises(
                ValueError, match="User ID is required for unassignment"
            ):
                manual_task_service.unassign_users_from_task(
                    task_id=manual_task.id, user_ids=unassign_users
                )
            return

        # Execute
        manual_task_service.unassign_users_from_task(
            task_id=manual_task.id, user_ids=unassign_users
        )

        # Verify references
        expected_ref_count = 1 + len(
            expected_remaining
        )  # parent entity + remaining users
        assert len(manual_task.references) == expected_ref_count

        verify_expected_reference_ids(
            manual_task,
            [manual_task.parent_entity_id] + expected_remaining,
        )
        verify_expected_reference_types(
            manual_task,
            [
                ManualTaskReferenceType.connection_config,
                ManualTaskReferenceType.assigned_user,
            ],
        )

        # Verify logs
        unassign_log = next(
            log for log in manual_task.logs if log.message == "Unassign users from task"
        )
        successfully_unassigned = sorted(list(set(initial_users) & set(unassign_users)))
        if successfully_unassigned:
            assert unassign_log.details["unassigned_users"] == successfully_unassigned
        if expected_not_unassigned:
            assert sorted(unassign_log.details["user_ids_not_unassigned"]) == sorted(
                expected_not_unassigned
            )


class TestManualTaskConfig:
    """Tests for the config-related methods."""

    def test_config_lifecycle(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_service: ManualTaskService,
    ):
        """Test the full lifecycle of a config - create and delete."""
        # Create config
        manual_task_service.create_config(
            task_id=manual_task.id,
            config_type=ManualTaskConfigurationType.access_privacy_request,
            fields=FIELDS,
        )

        # Verify config creation
        config = manual_task_service.config_service.get_current_config(
            task=manual_task,
            config_type=ManualTaskConfigurationType.access_privacy_request,
        )
        assert config is not None
        assert config.config_type == ManualTaskConfigurationType.access_privacy_request
        assert config.version == 1
        assert config.is_current is True
        assert len(config.field_definitions) == len(FIELDS)

        # Verify field definitions
        for field_key, expected_field in [
            (TEXT_FIELD_KEY, FIELDS[0]),
            (CHECKBOX_FIELD_KEY, FIELDS[1]),
            (ATTACHMENT_FIELD_KEY, FIELDS[2]),
        ]:
            field = next(
                field
                for field in config.field_definitions
                if field.field_key == field_key
            )
            assert (
                field.field_metadata["label"]
                == expected_field["field_metadata"]["label"]
            )

        # Verify creation logs
        logs = (
            db.query(ManualTaskLog)
            .filter_by(task_id=manual_task.id)
            .order_by(ManualTaskLog.created_at.desc())
            .all()
        )
        assert any(
            log.message == "Creating new configuration version"
            and log.status == ManualTaskLogStatus.complete
            and log.config_id == config.id
            for log in logs
        )

        # Delete config
        manual_task_service.delete_config(config=config, task_id=manual_task.id)
        db.commit()
        db.refresh(manual_task)

        # Verify deletion
        assert db.query(ManualTaskConfig).filter_by(id=config.id).first() is None

        # Query logs again after deletion
        logs = (
            db.query(ManualTaskLog)
            .filter_by(task_id=manual_task.id)
            .order_by(ManualTaskLog.created_at.desc())
            .all()
        )
        assert any(
            log.message == "Deleting Manual Task configuration"
            and log.status == ManualTaskLogStatus.complete
            for log in logs
        )
