from unittest.mock import Mock, patch

import pytest
from pydantic.v1.utils import deep_update

from fides.api.common_exceptions import AwaitingAsyncTaskCallback
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskSubmission,
    StatusType,
)
from fides.api.models.manual_task.conditional_dependency import (
    ManualTaskConditionalDependencyType,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request.request_task import RequestTask
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask


class TestManualTaskGraphTaskInitialization:
    """Test ManualTaskGraphTask initialization and basic functionality"""

    def test_initialization(self, task_resources):
        """Test that ManualTaskGraphTask initializes correctly"""
        graph_task = ManualTaskGraphTask(task_resources)
        assert hasattr(graph_task, "connection_key")
        assert (
            graph_task.connection_key
            == task_resources.privacy_request_task.dataset_name
        )

    def test_invalid_manual_task_address_raises_error(self, task_resources):
        """Test that invalid manual task addresses raise ValueError"""
        # Mock execution node with non-manual task address
        task_resources.privacy_request_task.collection_address = (
            "postgres_example:customer"
        )

        with pytest.raises(ValueError, match="Not a manual task address"):
            ManualTaskGraphTask(task_resources)

    @pytest.mark.usefixtures("connection_with_manual_access_task")
    def test_get_manual_task_or_none_with_valid_address(self, task_resources):
        """Test _get_manual_task_or_none with valid manual task address"""
        graph_task = ManualTaskGraphTask(task_resources)
        manual_task = graph_task._get_manual_task_or_none()

        assert manual_task is not None
        assert isinstance(manual_task, ManualTask)

    def test_get_manual_task_or_none_with_invalid_address(self, task_resources):
        """Test _get_manual_task_or_none with invalid address"""
        # Mock execution node with non-manual task address
        task_resources.privacy_request_task.collection_address = (
            "postgres_example:customer"
        )

        with pytest.raises(ValueError, match="Not a manual task address"):
            ManualTaskGraphTask(task_resources)._get_manual_task_or_none()


class TestManualTaskGraphTaskCoreMethods:
    """Test core methods of ManualTaskGraphTask"""

    def test_dry_run_task(self, task_resources):
        """Test dry_run_task returns expected value

        Manual tasks always return 1 for dry runs because they represent a single
        task that would be executed. Unlike data connectors that might process
        multiple records, manual tasks are atomic units that either execute
        completely or not at all. The value 1 indicates that one manual task
        instance would be created and processed during actual execution.
        """
        graph_task = ManualTaskGraphTask(task_resources)
        result = graph_task.dry_run_task()
        assert result == 1

    def test_check_manual_task_configs_with_valid_configs(
        self, task_resources, connection_with_manual_access_task
    ):
        """Test _check_manual_task_configs with valid configs"""
        graph_task = ManualTaskGraphTask(task_resources)
        _, manual_task, _, _ = connection_with_manual_access_task

        result = graph_task._check_manual_task_configs(
            manual_task,
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
        )
        assert result is True

    def test_check_manual_task_configs_with_no_configs(
        self, task_resources, connection_with_manual_access_task
    ):
        """Test _check_manual_task_configs with no valid configs"""
        graph_task = ManualTaskGraphTask(task_resources)
        _, manual_task, _, _ = connection_with_manual_access_task

        # Mark all configs as not current
        for config in manual_task.configs:
            config.is_current = False
            config.save(task_resources.session)

        result = graph_task._check_manual_task_configs(
            manual_task,
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
        )
        assert result is False

    def test_ensure_manual_task_instances_creates_new_instance(
        self, task_resources, connection_with_manual_access_task, access_privacy_request
    ):
        """Test _ensure_manual_task_instances creates new instance when none exists"""
        graph_task = ManualTaskGraphTask(task_resources)
        _, manual_task, _, _ = connection_with_manual_access_task

        # Verify no instances exist initially
        initial_count = len(access_privacy_request.manual_task_instances)

        graph_task._ensure_manual_task_instances(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Verify instance was created
        task_resources.session.refresh(access_privacy_request)
        assert len(access_privacy_request.manual_task_instances) == initial_count + 1

    def test_ensure_manual_task_instances_skips_existing_instance(
        self, task_resources, connection_with_manual_access_task, access_privacy_request
    ):
        """Test _ensure_manual_task_instances skips creation when instance already exists"""
        graph_task = ManualTaskGraphTask(task_resources)
        _, manual_task, config, _ = connection_with_manual_access_task

        # Create an instance first
        ManualTaskInstance.create(
            db=task_resources.session,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": StatusType.pending.value,
            },
        )

        initial_count = len(access_privacy_request.manual_task_instances)

        # Call again - should not create duplicate
        graph_task._ensure_manual_task_instances(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Verify no new instance was created
        task_resources.session.refresh(access_privacy_request)
        assert len(access_privacy_request.manual_task_instances) == initial_count

    def test_ensure_manual_task_instances_with_no_current_config(
        self, task_resources, connection_with_manual_access_task, access_privacy_request
    ):
        """Test _ensure_manual_task_instances handles case with no current config"""
        graph_task = ManualTaskGraphTask(task_resources)
        _, manual_task, _, _ = connection_with_manual_access_task

        # Mark all configs as not current
        for config in manual_task.configs:
            config.is_current = False
            config.save(task_resources.session)

        # Should not raise error and should not create instance
        initial_count = len(access_privacy_request.manual_task_instances)

        graph_task._ensure_manual_task_instances(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Verify no instance was created
        task_resources.session.refresh(access_privacy_request)
        assert len(access_privacy_request.manual_task_instances) == initial_count


class TestManualTaskGraphTaskRunRequest:
    """Test the _run_request method and its various scenarios"""

    def test_run_request_with_no_manual_task(self, task_resources):
        """Test _run_request when no manual task exists"""
        # Mock execution node with non-manual task address
        task_resources.privacy_request_task.collection_address = (
            "postgres_example:customer"
        )

        with pytest.raises(ValueError):
            ManualTaskGraphTask(task_resources)._run_request(
                ManualTaskConfigurationType.access_privacy_request, ActionType.access
            )

    @pytest.mark.usefixtures("condition_gt_18")
    def test_run_request_with_conditional_dependency_not_satisfied(
        self, task_resources, connection_with_manual_access_task
    ):
        """Test _run_request when conditional dependencies are not satisfied"""
        graph_task = ManualTaskGraphTask(task_resources)
        _, manual_task, _, _ = connection_with_manual_access_task

        # Don't pass inputs - the method should handle this gracefully
        result = graph_task._run_request(
            ManualTaskConfigurationType.access_privacy_request, ActionType.access
        )

        assert result is None

    def test_run_request_with_no_configs(
        self, task_resources, connection_with_manual_access_task
    ):
        """Test _run_request when manual task has no valid configs"""
        graph_task = ManualTaskGraphTask(task_resources)
        _, manual_task, _, _ = connection_with_manual_access_task

        # Mark all configs as not current
        for config in manual_task.configs:
            config.is_current = False
            config.save(task_resources.session)

        result = graph_task._run_request(
            ManualTaskConfigurationType.access_privacy_request, ActionType.access
        )

        assert result is None

    def test_run_request_with_incomplete_submissions(
        self, task_resources, connection_with_manual_access_task, access_privacy_request
    ):
        """Test _run_request raises AwaitingAsyncTaskCallback when submissions are incomplete"""
        graph_task = ManualTaskGraphTask(task_resources)
        _, manual_task, config, _ = connection_with_manual_access_task

        # Create instance without submissions
        ManualTaskInstance.create(
            db=task_resources.session,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": StatusType.pending.value,
            },
        )

        with pytest.raises(AwaitingAsyncTaskCallback):
            graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request, ActionType.access
            )

    def test_run_request_verifies_all_function_calls(
        self,
        connection_with_manual_access_task,
        access_privacy_request,
        build_graph_task,
    ):
        """Test _run_request makes all expected function calls with correct parameters"""
        _, graph_task = build_graph_task
        _, manual_task, config, field = connection_with_manual_access_task

        # Create completed instance with submission to ensure successful execution
        instance = ManualTaskInstance.create(
            db=graph_task.resources.session,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": StatusType.completed.value,
            },
        )

        ManualTaskSubmission.create(
            db=graph_task.resources.session,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "field_id": field.id,
                "instance_id": instance.id,
                "data": {"field_type": "text", "value": "user@example.com"},
            },
        )

        # Mock all the methods that _run_request calls
        with (
            patch.object(
                graph_task, "_get_manual_task_or_none"
            ) as mock_get_manual_task,
            patch.object(
                graph_task, "_get_conditional_data_and_evaluate"
            ) as mock_get_conditional_data,
            patch.object(
                graph_task, "_check_manual_task_configs"
            ) as mock_check_configs,
            patch.object(
                graph_task, "_ensure_manual_task_instances"
            ) as mock_ensure_instances,
            patch.object(
                graph_task, "_set_submitted_data_or_raise_awaiting_async_task_callback"
            ) as mock_set_submitted_data,
            patch.object(
                graph_task.resources.request.policy, "get_rules_for_action"
            ) as mock_get_rules,
        ):
            # Set up return values for successful execution
            mock_get_manual_task.return_value = manual_task
            mock_get_conditional_data.return_value = {"test": "data"}
            mock_check_configs.return_value = True
            mock_get_rules.return_value = [
                Mock()
            ]  # Return a list with at least one rule
            mock_set_submitted_data.return_value = [{"user_email": "user@example.com"}]

            # Call _run_request
            result = graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
                [{"test": "input"}],
            )

            # Verify all expected calls were made with correct parameters
            mock_get_manual_task.assert_called_once()

            mock_get_conditional_data.assert_called_once_with(
                manual_task, [{"test": "input"}]
            )

            mock_check_configs.assert_called_once_with(
                manual_task,
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
            )

            mock_get_rules.assert_called_once_with(action_type=ActionType.access)

            mock_ensure_instances.assert_called_once_with(
                manual_task,
                access_privacy_request,
                ManualTaskConfigurationType.access_privacy_request,
            )

            mock_set_submitted_data.assert_called_once_with(
                manual_task,
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
                conditional_data={"test": "data"},
            )

            # Verify the result
            assert result == [{"user_email": "user@example.com"}]

    def test_run_request_early_exit_when_no_manual_task(
        self,
        connection_with_manual_access_task,
        access_privacy_request,
        build_graph_task,
    ):
        """Test _run_request returns None early when no manual task is found"""
        _, graph_task = build_graph_task

        with patch.object(
            graph_task, "_get_manual_task_or_none"
        ) as mock_get_manual_task:
            mock_get_manual_task.return_value = None

            result = graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request, ActionType.access
            )

            # Should return None immediately
            assert result is None

            # Only _get_manual_task_or_none should be called
            mock_get_manual_task.assert_called_once()

    def test_run_request_early_exit_when_conditional_dependencies_not_satisfied(
        self,
        connection_with_manual_access_task,
        access_privacy_request,
        build_graph_task,
    ):
        """Test _run_request returns None when conditional dependencies are not satisfied"""
        _, graph_task = build_graph_task
        _, manual_task, _, _ = connection_with_manual_access_task

        with (
            patch.object(
                graph_task, "_get_manual_task_or_none"
            ) as mock_get_manual_task,
            patch.object(
                graph_task, "_get_conditional_data_and_evaluate"
            ) as mock_get_conditional_data,
        ):
            mock_get_manual_task.return_value = manual_task
            mock_get_conditional_data.return_value = None

            result = graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request, ActionType.access
            )

            # Should return None when conditional data is None
            assert result is None

            # Verify calls were made
            mock_get_manual_task.assert_called_once()
            mock_get_conditional_data.assert_called_once_with(manual_task)

    def test_run_request_early_exit_when_no_valid_configs(
        self,
        connection_with_manual_access_task,
        access_privacy_request,
        build_graph_task,
    ):
        """Test _run_request returns None when no valid configs exist"""
        _, graph_task = build_graph_task
        _, manual_task, _, _ = connection_with_manual_access_task

        with (
            patch.object(
                graph_task, "_get_manual_task_or_none"
            ) as mock_get_manual_task,
            patch.object(
                graph_task, "_get_conditional_data_and_evaluate"
            ) as mock_get_conditional_data,
            patch.object(
                graph_task, "_check_manual_task_configs"
            ) as mock_check_configs,
        ):
            mock_get_manual_task.return_value = manual_task
            mock_get_conditional_data.return_value = {"test": "data"}
            mock_check_configs.return_value = False

            result = graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request, ActionType.access
            )

            # Should return None when no valid configs
            assert result is None

            # Verify calls were made
            mock_get_manual_task.assert_called_once()
            mock_get_conditional_data.assert_called_once_with(manual_task)
            mock_check_configs.assert_called_once_with(
                manual_task,
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
            )

    def test_run_request_early_exit_when_no_policy_rules(
        self,
        connection_with_manual_access_task,
        access_privacy_request,
        build_graph_task,
    ):
        """Test _run_request returns None when no policy rules exist for action"""
        _, graph_task = build_graph_task
        _, manual_task, _, _ = connection_with_manual_access_task

        with (
            patch.object(
                graph_task, "_get_manual_task_or_none"
            ) as mock_get_manual_task,
            patch.object(
                graph_task, "_get_conditional_data_and_evaluate"
            ) as mock_get_conditional_data,
            patch.object(
                graph_task, "_check_manual_task_configs"
            ) as mock_check_configs,
            patch.object(
                graph_task.resources.request.policy, "get_rules_for_action"
            ) as mock_get_rules,
        ):
            mock_get_manual_task.return_value = manual_task
            mock_get_conditional_data.return_value = {"test": "data"}
            mock_check_configs.return_value = True
            mock_get_rules.return_value = []  # No rules

            result = graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request, ActionType.access
            )

            # Should return None when no policy rules
            assert result is None

            # Verify calls were made
            mock_get_manual_task.assert_called_once()
            mock_get_conditional_data.assert_called_once_with(manual_task)
            mock_check_configs.assert_called_once_with(
                manual_task,
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
            )
            mock_get_rules.assert_called_once_with(action_type=ActionType.access)


class TestManualTaskGraphTaskHelperMethods:
    """Test helper methods for data extraction and processing"""

    def test_extract_value_from_inputs_simple_field(self, task_resources):
        """Test _extract_value_from_inputs with simple field address"""
        graph_task = ManualTaskGraphTask(task_resources)
        inputs = [[{"name": "John", "age": 25}]]

        result = graph_task._extract_value_from_inputs("name", *inputs)
        assert result == "John"

        result = graph_task._extract_value_from_inputs("age", *inputs)
        assert result == 25

    def test_extract_value_from_inputs_nested_field(self, task_resources):
        """Test _extract_value_from_inputs with nested field address"""
        graph_task = ManualTaskGraphTask(task_resources)
        inputs = [[{"user": {"profile": {"age": 25, "name": "John"}}}]]

        result = graph_task._extract_value_from_inputs("user.profile.age", *inputs)
        assert result == 25

        result = graph_task._extract_value_from_inputs("user.profile.name", *inputs)
        assert result == "John"

    def test_extract_value_from_inputs_field_not_found(self, task_resources):
        """Test _extract_value_from_inputs when field is not found"""
        graph_task = ManualTaskGraphTask(task_resources)
        inputs = [[{"name": "John", "age": 25}]]

        result = graph_task._extract_value_from_inputs("email", *inputs)
        assert result is None

        result = graph_task._extract_value_from_inputs("user.profile.email", *inputs)
        assert result is None

    def test_extract_value_from_inputs_multiple_inputs(self, task_resources):
        """Test _extract_value_from_inputs with multiple input lists"""
        graph_task = ManualTaskGraphTask(task_resources)
        inputs = [
            [{"name": "John", "age": 25}],
            [{"email": "john@example.com", "city": "New York"}],
        ]

        result = graph_task._extract_value_from_inputs("name", *inputs)
        assert result == "John"

        result = graph_task._extract_value_from_inputs("email", *inputs)
        assert result == "john@example.com"

    def test_extract_value_from_inputs_empty_inputs(self, task_resources):
        """Test _extract_value_from_inputs with empty inputs"""
        graph_task = ManualTaskGraphTask(task_resources)
        inputs = []

        result = graph_task._extract_value_from_inputs("name", *inputs)
        assert result is None

    def test_get_nested_value_simple_path(self, task_resources):
        """Test _get_nested_value with simple path"""
        graph_task = ManualTaskGraphTask(task_resources)
        data = {"name": "John", "age": 25}

        result = graph_task._get_nested_value(data, ["name"])
        assert result == "John"

        result = graph_task._get_nested_value(data, ["age"])
        assert result == 25

    def test_get_nested_value_nested_path(self, task_resources):
        """Test _get_nested_value with nested path"""
        graph_task = ManualTaskGraphTask(task_resources)
        data = {"user": {"profile": {"age": 25, "name": "John"}}}

        result = graph_task._get_nested_value(data, ["user", "profile", "age"])
        assert result == 25

        result = graph_task._get_nested_value(data, ["user", "profile", "name"])
        assert result == "John"

    def test_get_nested_value_path_not_found(self, task_resources):
        """Test _get_nested_value when path is not found"""
        graph_task = ManualTaskGraphTask(task_resources)
        data = {"user": {"profile": {"age": 25}}}

        result = graph_task._get_nested_value(data, ["user", "profile", "email"])
        assert result is None

        result = graph_task._get_nested_value(data, ["user", "settings"])
        assert result is None

    def test_get_nested_value_empty_path(self, task_resources):
        """Test _get_nested_value with empty path"""
        graph_task = ManualTaskGraphTask(task_resources)
        data = {"name": "John"}

        result = graph_task._get_nested_value(data, [])
        assert result == data

    def test_get_nested_value_non_dict_intermediate(self, task_resources):
        """Test _get_nested_value when intermediate value is not a dict"""
        graph_task = ManualTaskGraphTask(task_resources)
        data = {"user": "John"}

        result = graph_task._get_nested_value(data, ["user", "profile"])
        assert result is None


class TestManualTaskGraphTaskSetNestedValue:
    """Test the _set_nested_value helper method"""

    def test_set_nested_value_simple_field(self, task_resources):
        """Test _set_nested_value with simple field address"""
        graph_task = ManualTaskGraphTask(task_resources)
        data = graph_task._set_nested_value("age", 25)

        assert data["age"] == 25

    def test_set_nested_value_nested_field(self, task_resources):
        """Test _set_nested_value with nested field address"""
        graph_task = ManualTaskGraphTask(task_resources)
        data = graph_task._set_nested_value("user.profile.age", 25)

        assert "user" in data
        assert "profile" in data["user"]
        assert data["user"]["profile"]["age"] == 25

    def test_set_nested_value_deeply_nested_field(self, task_resources):
        """Test _set_nested_value with deeply nested field address"""
        graph_task = ManualTaskGraphTask(task_resources)
        data = graph_task._set_nested_value("user.profile.address.city", "New York")

        assert data["user"]["profile"]["address"]["city"] == "New York"

    def test_set_nested_value_existing_structure(self, task_resources):
        """Test _set_nested_value with existing nested structure"""
        graph_task = ManualTaskGraphTask(task_resources)
        data = {"user": {"profile": {"name": "John"}}}

        result = graph_task._set_nested_value("user.profile.age", 25)
        data = deep_update(data, result)

        assert data["user"]["profile"]["name"] == "John"
        assert data["user"]["profile"]["age"] == 25
