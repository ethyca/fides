from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

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


class TestManualTaskGraphTaskAccessRequest:
    """Test the access_request method"""

    def test_access_request_with_no_manual_task(self, task_resources):
        """Test access_request when no manual task exists"""
        # Mock execution node with non-manual task address
        task_resources.privacy_request_task.collection_address = (
            "postgres_example:customer"
        )

        with pytest.raises(ValueError):
            ManualTaskGraphTask(task_resources).access_request()

    @pytest.mark.usefixtures("condition_gt_18", "connection_with_manual_access_task")
    def test_access_request_with_conditional_dependency_not_satisfied(
        self, task_resources
    ):
        """Test access_request returns empty list when conditional dependencies not satisfied"""
        graph_task = ManualTaskGraphTask(task_resources)

        # Pass input data that doesn't satisfy the condition
        inputs = [[{"profile": {"age": 15}}]]
        result = graph_task.access_request(*inputs)

        assert result == []

    def test_access_request_with_no_configs(
        self, task_resources, connection_with_manual_access_task
    ):
        """Test access_request returns empty list when no valid configs exist"""
        graph_task = ManualTaskGraphTask(task_resources)
        _, manual_task, _, _ = connection_with_manual_access_task

        # Mark all configs as not current
        for config in manual_task.configs:
            config.is_current = False
            config.save(task_resources.session)

        result = graph_task.access_request()

        assert result == []

    def test_access_request_returns_data_when_completed(
        self,
        connection_with_manual_access_task,
        access_privacy_request,
        build_graph_task,
    ):
        """Test access_request returns data when task is completed successfully"""
        _, graph_task = build_graph_task
        _, manual_task, config, field = connection_with_manual_access_task

        # Verify the policy has access rules
        policy = access_privacy_request.policy
        access_rules = policy.get_rules_for_action(ActionType.access)
        assert len(access_rules) > 0, "Policy must have access rules for this test"

        # First call should create the instance and return None (awaiting async callback)
        result = graph_task.access_request()
        assert result is None

        # Find the instance that was created
        instance = (
            graph_task.resources.session.query(ManualTaskInstance)
            .filter(
                ManualTaskInstance.task_id == manual_task.id,
                ManualTaskInstance.entity_id == access_privacy_request.id,
                ManualTaskInstance.config_id == config.id,
            )
            .first()
        )
        assert instance is not None

        # Create submission for the instance
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

        # Mark instance as completed
        instance.status = StatusType.completed
        instance.save(graph_task.resources.session)

        # Now call access_request again - should complete successfully and return data
        result = graph_task.access_request()
        assert isinstance(result, list)
        assert len(result) > 0


class TestManualTaskGraphTaskErasureRequest:
    """Test the erasure_request method"""

    def test_erasure_request_with_no_manual_task(self, task_resources):
        """Test erasure_request when no manual task exists"""
        # Mock execution node with non-manual task address
        task_resources.privacy_request_task.collection_address = (
            "postgres_example:customer"
        )

        with pytest.raises(ValueError):
            ManualTaskGraphTask(task_resources).erasure_request([])

    @pytest.mark.usefixtures("condition_gt_18", "connection_with_manual_erasure_task")
    def test_erasure_request_with_conditional_dependency_not_satisfied(
        self, task_resources
    ):
        """Test erasure_request returns 0 when conditional dependencies not satisfied"""
        graph_task = ManualTaskGraphTask(task_resources)

        # Pass input data that doesn't satisfy the condition
        inputs = [[{"profile": {"age": 15}}]]

        result = graph_task.erasure_request([], inputs=inputs)

        assert result == 0

    def test_erasure_request_with_no_configs(
        self, task_resources, connection_with_manual_erasure_task
    ):
        """Test erasure_request returns 0 when no valid configs exist"""
        graph_task = ManualTaskGraphTask(task_resources)
        _, manual_task, _, _ = connection_with_manual_erasure_task

        # Mark all configs as not current
        for config in manual_task.configs:
            config.is_current = False
            config.save(task_resources.session)

        result = graph_task.erasure_request([])

        assert result == 0

    def test_erasure_request_sets_rows_masked_to_zero(
        self,
        connection_with_manual_erasure_task,
        erasure_privacy_request,
        build_erasure_graph_task,
    ):
        """Test erasure_request sets rows_masked to 0 when successful"""
        _, graph_task = build_erasure_graph_task
        _, manual_task, config, field = connection_with_manual_erasure_task

        # Verify the policy has erasure rules
        policy = erasure_privacy_request.policy
        erasure_rules = policy.get_rules_for_action(ActionType.erasure)
        assert len(erasure_rules) > 0, "Policy must have erasure rules for this test"

        # First call should create the instance and return None (awaiting async callback)
        result = graph_task.erasure_request([], inputs=[])
        assert result is None

        # Find the instance that was created
        instance = (
            graph_task.resources.session.query(ManualTaskInstance)
            .filter(
                ManualTaskInstance.task_id == manual_task.id,
                ManualTaskInstance.entity_id == erasure_privacy_request.id,
                ManualTaskInstance.config_id == config.id,
            )
            .first()
        )
        assert instance is not None

        # Create submission for the instance
        ManualTaskSubmission.create(
            db=graph_task.resources.session,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "field_id": field.id,
                "instance_id": instance.id,
                "data": {"field_type": "text", "value": "erasure confirmed"},
            },
        )

        # Mark instance as completed
        instance.status = StatusType.completed
        instance.save(graph_task.resources.session)

        # Now call erasure_request again - should complete successfully and set rows_masked
        result = graph_task.erasure_request([], inputs=[])
        assert result == 0

        # Query the request task from the database to see the updated rows_masked value
        request_task = (
            graph_task.resources.session.query(RequestTask)
            .filter(RequestTask.id == graph_task.request_task.id)
            .first()
        )
        assert request_task.rows_masked == 0
