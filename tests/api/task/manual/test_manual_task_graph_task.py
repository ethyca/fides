from unittest.mock import patch

import pytest
from pytest import param

from fides.api.common_exceptions import AwaitingAsyncTaskCallback
from fides.api.models.manual_task import (
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.models.manual_task.conditional_dependency import (
    ManualTaskConditionalDependency,
)
from fides.api.schemas.policy import ActionType
from fides.api.task.conditional_dependencies.schemas import (
    ConditionEvaluationResult,
    GroupEvaluationResult,
)


class TestManualTaskDataAggregation:
    """Test the data aggregation methods in ManualTaskGraphTask"""

    @pytest.fixture
    def manual_task_instance_with_field(
        self, db, access_privacy_request, connection_with_manual_access_task
    ):
        """Create a manual task instance with proper field setup"""
        _, manual_task, config, field = connection_with_manual_access_task
        return ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

    def test_aggregate_submission_data_empty_instances(self, manual_task_graph_task):
        """Test aggregation with empty instances list"""
        result = manual_task_graph_task._aggregate_submission_data([])
        assert result == {}

    def test_aggregate_submission_data_no_submissions(
        self, manual_task_graph_task, manual_task_instance_with_field
    ):
        """Test aggregation with instances that have no submissions"""
        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

    def test_aggregate_submission_data_text_field(
        self, manual_task_graph_task, manual_task_submission_text
    ):
        """Test aggregation with text field submission"""
        # Get the instance from the submission
        instance = manual_task_submission_text.instance

        result = manual_task_graph_task._aggregate_submission_data([instance])

        assert "user_email" in result
        assert result["user_email"] == "user@example.com"

    def test_aggregate_submission_data_checkbox_field(
        self, manual_task_graph_task, manual_task_submission_checkbox
    ):
        """Test aggregation with checkbox field submission"""
        # Get the instance from the submission
        instance = manual_task_submission_checkbox.instance

        result = manual_task_graph_task._aggregate_submission_data([instance])

        assert "user_email" in result
        assert result["user_email"] is True

    def test_aggregate_submission_data_multiple_instances(
        self,
        manual_task_graph_task,
        manual_task_submission_text,
        manual_task_submission_checkbox,
    ):
        """Test aggregation with multiple instances"""
        instance1 = manual_task_submission_text.instance
        instance2 = manual_task_submission_checkbox.instance

        result = manual_task_graph_task._aggregate_submission_data(
            [instance1, instance2]
        )

        # Should have data from both instances
        assert "user_email" in result
        # The last instance processed will overwrite the first one with the same field_key
        assert result["user_email"] is True

    def test_aggregate_submission_data_invalid_submission_data(
        self,
        manual_task_graph_task,
        manual_task_instance_with_field,
        connection_with_manual_access_task,
    ):
        """Test aggregation with invalid submission data"""
        # Get the field from the connection setup
        _, _, config, field = connection_with_manual_access_task

        # Create a submission with invalid data structure
        submission = ManualTaskSubmission(
            task_id=manual_task_instance_with_field.task_id,
            config_id=manual_task_instance_with_field.config_id,
            field_id=field.id,
            instance_id=manual_task_instance_with_field.id,
            submitted_by=None,
            data="invalid_data",  # Not a dict
        )
        manual_task_instance_with_field.submissions = [submission]

        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

    def test_aggregate_submission_data_missing_field_key(
        self,
        manual_task_graph_task,
        manual_task_instance_with_field,
        connection_with_manual_access_task,
    ):
        """Test aggregation with submission missing field_key"""
        # Get the field from the connection setup
        _, _, config, field = connection_with_manual_access_task

        # Create a submission with field but no field_key
        submission = ManualTaskSubmission(
            task_id=manual_task_instance_with_field.task_id,
            config_id=manual_task_instance_with_field.config_id,
            field_id=field.id,
            instance_id=manual_task_instance_with_field.id,
            submitted_by=None,
            data={"field_type": ManualTaskFieldType.text.value, "value": "test"},
        )
        # Temporarily set field_key to None for testing (will be restored)
        original_field_key = field.field_key
        field.field_key = None
        submission.field = field
        manual_task_instance_with_field.submissions = [submission]

        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

        # Restore the original field_key
        field.field_key = original_field_key

    @patch("fides.api.task.manual.manual_task_graph_task.format_size")
    def test_process_attachment_field_success(
        self,
        mock_format_size,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test successful attachment field processing"""
        mock_format_size.return_value = "1.2 KB"

        # Mock the attachment retrieval
        with patch.object(
            attachment_for_access_package, "retrieve_attachment"
        ) as mock_retrieve:
            mock_retrieve.return_value = (1234, "https://example.com/file.pdf")

            result = manual_task_graph_task._process_attachment_field(
                manual_task_submission_attachment
            )

            assert result is not None
            assert "test_document.pdf" in result
            assert result["test_document.pdf"]["url"] == "https://example.com/file.pdf"
            assert result["test_document.pdf"]["size"] == "1.2 KB"

    def test_process_attachment_field_no_attachments(
        self, manual_task_graph_task, manual_task_submission_attachment
    ):
        """Test attachment field processing with no attachments"""
        # Clear attachments
        manual_task_submission_attachment.attachments = []

        result = manual_task_graph_task._process_attachment_field(
            manual_task_submission_attachment
        )
        assert result is None

    def test_process_attachment_field_wrong_attachment_type(
        self,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test attachment field processing with wrong attachment type"""
        # Change the attachment type to internal_use_only (not include_with_access_package)
        attachment_for_access_package.attachment_type = "internal_use_only"

        result = manual_task_graph_task._process_attachment_field(
            manual_task_submission_attachment
        )
        assert result is None

    @patch("fides.api.task.manual.manual_task_graph_task.logger")
    def test_process_attachment_field_retrieval_error(
        self,
        mock_logger,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test attachment field processing with retrieval error"""
        # Mock the attachment retrieval to raise an exception
        with patch.object(
            attachment_for_access_package, "retrieve_attachment"
        ) as mock_retrieve:
            mock_retrieve.side_effect = Exception("Storage error")

            result = manual_task_graph_task._process_attachment_field(
                manual_task_submission_attachment
            )

            # Should log warning and continue
            mock_logger.warning.assert_called_once()
            assert result is None

    @patch("fides.api.task.manual.manual_task_graph_task.format_size")
    def test_process_attachment_field_multiple_attachments(
        self,
        mock_format_size,
        manual_task_graph_task,
        manual_task_submission_attachment,
        multiple_attachments_for_access,
    ):
        """Test attachment field processing with multiple attachments"""
        mock_format_size.return_value = "2.5 KB"

        # Mock the attachment retrieval for multiple attachments
        with (
            patch.object(
                multiple_attachments_for_access[0], "retrieve_attachment"
            ) as mock_retrieve1,
            patch.object(
                multiple_attachments_for_access[1], "retrieve_attachment"
            ) as mock_retrieve2,
        ):

            mock_retrieve1.return_value = (2560, "https://example.com/doc1.pdf")
            mock_retrieve2.return_value = (1024, "https://example.com/doc2.pdf")

            result = manual_task_graph_task._process_attachment_field(
                manual_task_submission_attachment
            )

            assert result is not None
            assert "document1.pdf" in result
            assert "document2.pdf" in result
            assert result["document1.pdf"]["url"] == "https://example.com/doc1.pdf"
            assert result["document2.pdf"]["url"] == "https://example.com/doc2.pdf"
            assert result["document1.pdf"]["size"] == "2.5 KB"
            assert result["document2.pdf"]["size"] == "2.5 KB"

    def test_aggregate_submission_data_with_attachment_field(
        self,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test aggregation with attachment field submission"""
        # Get the instance from the submission
        instance = manual_task_submission_attachment.instance

        # Mock the attachment retrieval
        with patch.object(
            attachment_for_access_package, "retrieve_attachment"
        ) as mock_retrieve:
            mock_retrieve.return_value = (1234, "https://example.com/file.pdf")

            result = manual_task_graph_task._aggregate_submission_data([instance])

            # Should process attachment field
            assert "user_email" in result
            assert isinstance(result["user_email"], dict)
            assert "test_document.pdf" in result["user_email"]

    def test_aggregate_submission_data_mixed_field_types(
        self,
        manual_task_graph_task,
        manual_task_submission_text,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test aggregation with mixed field types (text and attachment)"""
        instance1 = manual_task_submission_text.instance
        instance2 = manual_task_submission_attachment.instance

        # Mock the attachment retrieval
        with patch.object(
            attachment_for_access_package, "retrieve_attachment"
        ) as mock_retrieve:
            mock_retrieve.return_value = (1234, "https://example.com/file.pdf")

            result = manual_task_graph_task._aggregate_submission_data(
                [instance1, instance2]
            )

            # Should have both text and attachment data
            assert "user_email" in result
            # The last instance processed will overwrite the first one with the same field_key
            assert isinstance(result["user_email"], dict)
            assert "test_document.pdf" in result["user_email"]

    def test_aggregate_submission_data_attachment_field_no_attachments(
        self, manual_task_graph_task, manual_task_submission_attachment
    ):
        """Test aggregation with attachment field but no attachments"""
        # Get the instance from the submission
        instance = manual_task_submission_attachment.instance

        # Clear attachments
        manual_task_submission_attachment.attachments = []

        result = manual_task_graph_task._aggregate_submission_data([instance])

        # Should return None for attachment field with no attachments
        assert "user_email" in result
        assert result["user_email"] is None

    def test_aggregate_submission_data_invalid_submission_data_type(
        self,
        manual_task_graph_task,
        manual_task_instance_with_field,
        connection_with_manual_access_task,
    ):
        """Test aggregation with submission data that is not a dict"""
        _, _, config, field = connection_with_manual_access_task

        # Create submission with non-dict data
        submission = ManualTaskSubmission(
            task_id=manual_task_instance_with_field.task_id,
            config_id=manual_task_instance_with_field.config_id,
            field_id=field.id,
            instance_id=manual_task_instance_with_field.id,
            submitted_by=None,
            data="not_a_dict",  # Invalid data type
        )
        manual_task_instance_with_field.submissions = [submission]

        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

    def test_aggregate_submission_data_missing_field_type(
        self,
        manual_task_graph_task,
        manual_task_instance_with_field,
        connection_with_manual_access_task,
    ):
        """Test aggregation with submission missing field_type"""
        _, _, config, field = connection_with_manual_access_task

        # Create submission without field_type
        submission = ManualTaskSubmission(
            task_id=manual_task_instance_with_field.task_id,
            config_id=manual_task_instance_with_field.config_id,
            field_id=field.id,
            instance_id=manual_task_instance_with_field.id,
            submitted_by=None,
            data={"value": "test_value"},  # Missing field_type
        )
        manual_task_instance_with_field.submissions = [submission]

        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}


class TestManualTaskConditionalDependencies:
    """Test that Manual Tasks only create instances when conditional dependencies are met"""

    @pytest.fixture
    def mock_conditional_evaluation(self, build_graph_task):
        """Create a mock for _get_conditional_data_and_evaluate with autospec"""
        manual_task, graph_task = build_graph_task
        with patch.object(
            graph_task, "_get_conditional_data_and_evaluate", autospec=True
        ) as mock_evaluate:
            yield mock_evaluate, manual_task, graph_task

    @pytest.fixture
    def evaluation_result(self):
        return ConditionEvaluationResult(
            result=True,
            message="Conditions met",
            field_address="postgres_example:customer:profile:age",
            operator="gte",
            expected_value=18,
            actual_value=25,
        )

    @pytest.fixture
    def group_evaluation_result(self, evaluation_result):
        return GroupEvaluationResult(
            logical_operator="and",
            result=True,
            condition_results=[evaluation_result, evaluation_result],
        )

    def test_manual_task_creates_instance_when_condition_met(
        self,
        db,
        mock_conditional_evaluation,
        access_privacy_request,
        evaluation_result,
    ):
        """Test that manual task instances are created when conditional dependencies are satisfied"""
        mock_evaluate, manual_task, graph_task = mock_conditional_evaluation

        # Configure mock to return satisfying data in the expected tuple format
        mock_evaluate.return_value = ({"test": "data"}, evaluation_result)

        # Verify no instances exist initially
        initial_instances = access_privacy_request.manual_task_instances
        assert len(initial_instances) == 0

        # Call _run_request which should create instances when conditions are met
        # This should raise AwaitingAsyncTaskCallback since no submissions exist yet
        with pytest.raises(AwaitingAsyncTaskCallback):
            graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
                [],  # Empty input data since we're mocking the extraction
            )

        # Refresh the privacy request to get updated instances
        db.refresh(access_privacy_request)

        # Verify that instances were created
        updated_instances = access_privacy_request.manual_task_instances
        assert len(updated_instances) == 1
        assert updated_instances[0].task_id == manual_task.id

    def test_manual_task_does_not_create_instance_when_condition_not_met(
        self,
        db,
        mock_conditional_evaluation,
        access_privacy_request,
        evaluation_result,
    ):
        """Test that manual task instances are NOT created when conditional dependencies are not satisfied"""
        mock_evaluate, manual_task, graph_task = mock_conditional_evaluation

        # Configure mock to return None (conditions not met) in the expected tuple format
        evaluation_result.result = False
        mock_evaluate.return_value = (None, evaluation_result)

        # Verify no instances exist initially
        initial_instances = access_privacy_request.manual_task_instances
        assert len(initial_instances) == 0

        # Call _run_request which should NOT create instances when conditions are not met
        result = graph_task._run_request(
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
            [],  # Empty input data since we're mocking the extraction
        )

        # Should return None when conditions are not met
        assert result is None

        # Refresh the privacy request to get updated instances
        db.refresh(access_privacy_request)

        # Verify that NO instances were created
        updated_instances = access_privacy_request.manual_task_instances
        assert len(updated_instances) == 0

    def test_manual_task_with_multiple_conditions_all_met(
        self,
        db,
        mock_conditional_evaluation,
        access_privacy_request,
        group_evaluation_result,
    ):
        """Test that manual task instances are created when ALL conditional dependencies are satisfied"""
        mock_evaluate, manual_task, graph_task = mock_conditional_evaluation

        # Configure mock to return data satisfying ALL conditions in the expected tuple format
        mock_evaluate.return_value = ({"test": "data"}, group_evaluation_result)

        # Verify no instances exist initially
        initial_instances = access_privacy_request.manual_task_instances
        assert len(initial_instances) == 0

        # Call _run_request which should create instances when all conditions are met
        # This should raise AwaitingAsyncTaskCallback since no submissions exist yet
        with pytest.raises(AwaitingAsyncTaskCallback):
            graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
                [],  # Empty input data since we're mocking the extraction
            )

        # Refresh the privacy request to get updated instances
        db.refresh(access_privacy_request)

        # Verify that instances were created
        updated_instances = access_privacy_request.manual_task_instances
        assert len(updated_instances) == 1
        assert updated_instances[0].task_id == manual_task.id

    def test_manual_task_with_no_conditional_dependencies(
        self,
        db,
        mock_conditional_evaluation,
        access_privacy_request,
    ):
        """Test that manual task instances are always created when there are no conditional dependencies"""
        mock_evaluate, manual_task, graph_task = mock_conditional_evaluation

        # Configure mock to return empty data (no conditions)
        mock_evaluate.return_value = ({}, None)  # No conditional dependencies

        # Verify no instances exist initially
        initial_instances = access_privacy_request.manual_task_instances
        assert len(initial_instances) == 0

        # Call _run_request which should create instances when there are no conditions
        # This should raise AwaitingAsyncTaskCallback since no submissions exist yet
        with pytest.raises(AwaitingAsyncTaskCallback):
            graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
                [],  # Empty input data since we're mocking the extraction
            )

        # Refresh the privacy request to get updated instances
        db.refresh(access_privacy_request)

        # Verify that instances were created (no conditions means always execute)
        updated_instances = access_privacy_request.manual_task_instances
        assert len(updated_instances) == 1
        assert updated_instances[0].task_id == manual_task.id


class TestManualTaskDataExtraction:
    """Test the _extract_conditional_dependency_data_from_inputs method in ManualTaskGraphTask"""

    def setup_method(self):
        """Import CollectionAddress for all test methods"""
        from fides.api.graph.config import CollectionAddress

        self.CollectionAddress = CollectionAddress

    def test_extract_conditional_dependency_data_from_inputs_simple_field(
        self, manual_task_graph_task, db, manual_task
    ):
        """Test extracting a simple field like 'postgres_example_test_dataset:customer:email'"""
        # Mock the execution node to have specific input keys
        with patch.object(
            manual_task_graph_task, "execution_node", autospec=True
        ) as mock_node:
            mock_node.input_keys = [
                self.CollectionAddress.from_string(
                    "postgres_example_test_dataset:customer"
                )
            ]

            # Create test input data
            inputs = [
                [
                    {"id": 1, "email": "customer-1@example.com", "name": "Customer 1"},
                    {"id": 2, "email": "customer-2@example.com", "name": "Customer 2"},
                ]
            ]

            # Create a conditional dependency that references the email field
            from fides.api.models.manual_task.conditional_dependency import (
                ManualTaskConditionalDependency,
            )

            dependency = ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": "leaf",
                    "field_address": "postgres_example_test_dataset:customer:email",
                    "operator": "exists",
                    "value": None,
                    "sort_order": 1,
                },
            )

            # Extract the data
            result = (
                manual_task_graph_task._extract_conditional_dependency_data_from_inputs(
                    *inputs, manual_task=manual_task
                )
            )

            # Should extract the email field data
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {
                        "email": "customer-1@example.com"  # First non-None value found
                    }
                }
            }
            assert result == expected

    def test_extract_conditional_dependency_data_from_inputs_nested_field(
        self, manual_task_graph_task, db, manual_task
    ):
        """Test extracting nested fields like 'dataset:collection:subcollection:field'"""
        # Mock the execution node to have specific input keys
        with patch.object(
            manual_task_graph_task, "execution_node", autospec=True
        ) as mock_node:
            mock_node.input_keys = [
                self.CollectionAddress.from_string(
                    "postgres_example_test_dataset:customer"
                )
            ]

            # Create test input data with nested structure
            inputs = [
                [{"id": 1, "profile": {"age": 25, "preferences": {"theme": "dark"}}}]
            ]

            # Create a conditional dependency that references a deeply nested field
            from fides.api.models.manual_task.conditional_dependency import (
                ManualTaskConditionalDependency,
            )

            dependency = ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": "leaf",
                    "field_address": "postgres_example_test_dataset:customer:profile:preferences:theme",
                    "operator": "eq",
                    "value": "dark",
                    "sort_order": 1,
                },
            )

            # Extract the data
            result = (
                manual_task_graph_task._extract_conditional_dependency_data_from_inputs(
                    *inputs, manual_task=manual_task
                )
            )

            # Should extract the nested field data
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"profile": {"preferences": {"theme": "dark"}}}
                }
            }
            assert result == expected

    def test_extract_conditional_dependency_data_from_inputs_missing_field(
        self, manual_task_graph_task, db, manual_task
    ):
        """Test behavior when the field doesn't exist in input data"""
        # Mock the execution node to have specific input keys
        with patch.object(
            manual_task_graph_task, "execution_node", autospec=True
        ) as mock_node:
            mock_node.input_keys = [
                self.CollectionAddress.from_string(
                    "postgres_example_test_dataset:customer"
                )
            ]

            # Create test input data without the expected field
            inputs = [[{"id": 1, "name": "Customer 1"}]]  # No email field

            # Create a conditional dependency that references a missing field
            from fides.api.models.manual_task.conditional_dependency import (
                ManualTaskConditionalDependency,
            )

            dependency = ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": "leaf",
                    "field_address": "postgres_example_test_dataset:customer:email",
                    "operator": "exists",
                    "value": None,
                    "sort_order": 1,
                },
            )

            # Extract the data
            result = (
                manual_task_graph_task._extract_conditional_dependency_data_from_inputs(
                    *inputs, manual_task=manual_task
                )
            )

            # Should include the field with None value
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"email": None}  # Field not found, so None
                }
            }
            assert result == expected

    def test_extract_conditional_dependency_data_from_inputs_multiple_collections(
        self, manual_task_graph_task, db, manual_task
    ):
        """Test extracting from multiple input collections"""
        # Mock the execution node to have multiple input keys
        with patch.object(
            manual_task_graph_task, "execution_node", autospec=True
        ) as mock_node:
            mock_node.input_keys = [
                self.CollectionAddress.from_string(
                    "postgres_example_test_dataset:customer"
                ),
                self.CollectionAddress.from_string(
                    "postgres_example_test_dataset:address"
                ),
            ]

            # Create test input data for multiple collections
            inputs = [
                [{"id": 1, "email": "customer-1@example.com"}],  # customer collection
                [{"id": 1, "city": "New York"}],  # address collection
            ]

            # Create conditional dependencies that reference both collections
            from fides.api.models.manual_task.conditional_dependency import (
                ManualTaskConditionalDependency,
            )

            ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": "leaf",
                    "field_address": "postgres_example_test_dataset:customer:email",
                    "operator": "exists",
                    "value": None,
                    "sort_order": 1,
                },
            )
            ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": "leaf",
                    "field_address": "postgres_example_test_dataset:address:city",
                    "operator": "eq",
                    "value": "New York",
                    "sort_order": 2,
                },
            )

            # Extract the data
            result = (
                manual_task_graph_task._extract_conditional_dependency_data_from_inputs(
                    *inputs, manual_task=manual_task
                )
            )

            # Should extract data from both collections
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"email": "customer-1@example.com"},
                    "address": {"city": "New York"},
                }
            }
            assert result == expected

    def test_extract_conditional_dependency_data_from_inputs_field_address_parsing(
        self, manual_task_graph_task, db, manual_task
    ):
        """Test that FieldAddress.from_string() works correctly"""
        # Mock the execution node to have specific input keys
        with patch.object(
            manual_task_graph_task, "execution_node", autospec=True
        ) as mock_node:
            mock_node.input_keys = [
                self.CollectionAddress.from_string(
                    "postgres_example_test_dataset:customer"
                )
            ]

            # Create test input data
            inputs = [[{"id": 1, "email": "customer-1@example.com"}]]

            # Create a conditional dependency with a complex field address
            from fides.api.models.manual_task.conditional_dependency import (
                ManualTaskConditionalDependency,
            )

            dependency = ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": "leaf",
                    "field_address": "postgres_example_test_dataset:customer:email",
                    "operator": "exists",
                    "value": None,
                    "sort_order": 1,
                },
            )

            # Extract the data
            result = (
                manual_task_graph_task._extract_conditional_dependency_data_from_inputs(
                    *inputs, manual_task=manual_task
                )
            )

            # Should correctly parse the field address and extract the data
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"email": "customer-1@example.com"}
                }
            }
            assert result == expected

    def test_extract_conditional_dependency_data_from_inputs_empty_inputs(
        self, manual_task_graph_task, db, manual_task
    ):
        """Test behavior with empty input data"""
        # Mock the execution node to have specific input keys
        with patch.object(
            manual_task_graph_task, "execution_node", autospec=True
        ) as mock_node:
            mock_node.input_keys = [
                self.CollectionAddress.from_string(
                    "postgres_example_test_dataset:customer"
                )
            ]

            # Create empty input data
            inputs = [[]]  # Empty list for the collection

            # Create a conditional dependency
            from fides.api.models.manual_task.conditional_dependency import (
                ManualTaskConditionalDependency,
            )

            dependency = ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_type": "leaf",
                    "field_address": "postgres_example_test_dataset:customer:email",
                    "operator": "exists",
                    "value": None,
                    "sort_order": 1,
                },
            )

            # Extract the data
            result = (
                manual_task_graph_task._extract_conditional_dependency_data_from_inputs(
                    *inputs, manual_task=manual_task
                )
            )

            # Should handle empty inputs gracefully
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"email": None}  # No data to extract
                }
            }
            assert result == expected

    def test_extract_conditional_dependency_data_from_inputs_no_conditional_dependencies(
        self, manual_task_graph_task, db, manual_task
    ):
        """Test behavior when there are no conditional dependencies"""
        # Mock the execution node to have specific input keys
        with patch.object(
            manual_task_graph_task, "execution_node", autospec=True
        ) as mock_node:
            mock_node.input_keys = [
                self.CollectionAddress.from_string(
                    "postgres_example_test_dataset:customer"
                )
            ]

            # Create test input data
            inputs = [[{"id": 1, "email": "customer-1@example.com"}]]

            # No conditional dependencies created

            # Extract the data
            result = (
                manual_task_graph_task._extract_conditional_dependency_data_from_inputs(
                    *inputs, manual_task=manual_task
                )
            )

            # Should return empty dict when no conditional dependencies exist
            assert result == {}

    @pytest.mark.parametrize(
        "field_address,expected_source_collection_key,expected_field_path",
        [
            param(
                "postgres_example:customer:profile:preferences:theme",
                "postgres_example:customer",
                ["profile", "preferences", "theme"],
                id="complex_nested",
            ),
            param(
                "postgres_example:customer:email",
                "postgres_example:customer",
                ["email"],
                id="simple",
            ),
        ],
    )
    def test_parse_field_address(
        self,
        manual_task_graph_task,
        field_address,
        expected_source_collection_key,
        expected_field_path,
    ):
        """Test parsing field addresses with various formats and edge cases"""
        source_collection_key, field_path = manual_task_graph_task._parse_field_address(
            field_address
        )

        assert source_collection_key == expected_source_collection_key
        assert field_path == expected_field_path

    @pytest.mark.parametrize(
        "data,field_path,expected_result",
        [
            param({"test": "value"}, [], {"test": "value"}, id="empty_path"),
            param({"test": "value"}, ["missing"], None, id="missing_field"),
            param(
                {"test": {"nested": "value"}},
                ["test", "nested"],
                "value",
                id="nested_dict",
            ),
            param(
                {"test": "value"},
                ["test", "nested"],
                None,
                id="nested_dict_missing_field",
            ),
        ],
    )
    def test_extract_nested_field_value(
        self, manual_task_graph_task, data, field_path, expected_result
    ):
        """Test extracting nested field value with empty field path"""
        result = manual_task_graph_task._extract_nested_field_value(data, field_path)
        assert result == expected_result

    @pytest.mark.parametrize(
        "field_address,expected_result",
        [
            param(
                "dataset:collection:field",
                {"dataset": {"collection": {"field": "test_value"}}},
                id="simple",
            ),
            param(
                "dataset:collection:nested:subnested:field",
                {
                    "dataset": {
                        "collection": {"nested": {"subnested": {"field": "test_value"}}}
                    }
                },
                id="complex",
            ),
            param("invalid_format", {"invalid_format": "test_value"}, id="fallback"),
        ],
    )
    def test_set_nested_value(
        self, manual_task_graph_task, field_address, expected_result
    ):
        """Test setting nested value for simple 3-part field address"""
        value = "test_value"
        result = manual_task_graph_task._set_nested_value(field_address, value)
        assert result == expected_result

    def test_evaluate_conditional_dependencies_no_root_condition(
        self, manual_task_graph_task, db, manual_task
    ):
        """Test evaluating conditional dependencies when no root condition exists"""
        with patch.object(
            ManualTaskConditionalDependency, "get_root_condition", return_value=None
        ):
            result = manual_task_graph_task._evaluate_conditional_dependencies(
                manual_task, {"test": "data"}
            )
            assert result is None

    def test_evaluate_conditional_dependencies_with_root_condition(
        self, manual_task_graph_task, db, manual_task
    ):
        """Test evaluating conditional dependencies with existing root condition"""
        mock_root_condition = "mock_condition"
        mock_evaluation_result = "mock_result"

        with (
            patch.object(
                ManualTaskConditionalDependency,
                "get_root_condition",
                return_value=mock_root_condition,
            ),
            patch(
                "fides.api.task.manual.manual_task_graph_task.ConditionEvaluator"
            ) as mock_evaluator_class,
        ):
            mock_evaluator = mock_evaluator_class.return_value
            mock_evaluator.evaluate_rule.return_value = mock_evaluation_result

            result = manual_task_graph_task._evaluate_conditional_dependencies(
                manual_task, {"test": "data"}
            )
            assert result == mock_evaluation_result

    def test_get_conditional_data_and_evaluate_no_evaluation_result(
        self, manual_task_graph_task, manual_task
    ):
        """Test getting conditional data when evaluation result is None"""
        with (
            patch.object(
                manual_task_graph_task,
                "_extract_conditional_dependency_data_from_inputs",
                return_value={"test": "data"},
            ),
            patch.object(
                manual_task_graph_task,
                "_evaluate_conditional_dependencies",
                return_value=None,
            ),
        ):
            conditional_data, evaluation_result = (
                manual_task_graph_task._get_conditional_data_and_evaluate(
                    manual_task, []
                )
            )
            assert conditional_data == {"test": "data"}
            assert evaluation_result is None

    def test_get_conditional_data_and_evaluate_conditions_not_met(
        self, manual_task_graph_task, manual_task
    ):
        """Test getting conditional data when conditions are not met"""
        mock_evaluation_result = type("MockResult", (), {"result": False})()

        with (
            patch.object(
                manual_task_graph_task,
                "_extract_conditional_dependency_data_from_inputs",
                return_value={"test": "data"},
            ),
            patch.object(
                manual_task_graph_task,
                "_evaluate_conditional_dependencies",
                return_value=mock_evaluation_result,
            ),
            patch.object(manual_task_graph_task, "update_status") as mock_update_status,
        ):
            conditional_data, evaluation_result = (
                manual_task_graph_task._get_conditional_data_and_evaluate(
                    manual_task, []
                )
            )
            assert conditional_data is None
            assert evaluation_result == mock_evaluation_result
            mock_update_status.assert_called_once()

    def test_check_manual_task_configs_no_configs(
        self, manual_task_graph_task, manual_task
    ):
        """Test checking manual task configs when no configs exist"""
        # Clear existing configs
        manual_task.configs = []

        with patch.object(
            manual_task_graph_task, "log_end", autospec=True
        ) as mock_log_end:
            result = manual_task_graph_task._check_manual_task_configs(
                manual_task,
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
            )
            assert result is False
            mock_log_end.assert_called_once_with(ActionType.access)

    def test_check_manual_task_configs_with_configs(
        self, manual_task_graph_task, connection_with_manual_access_task
    ):
        """Test checking manual task configs when configs exist"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Ensure configs exist and are current
        config.is_current = True
        config.config_type = ManualTaskConfigurationType.access_privacy_request

        result = manual_task_graph_task._check_manual_task_configs(
            manual_task,
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
        )
        assert result is True

    def test_ensure_manual_task_instances_existing_instance(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test ensuring manual task instances when instance already exists"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Create an existing instance
        existing_instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # This should not create a new instance
        manual_task_graph_task._ensure_manual_task_instances(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Verify only one instance exists
        instances = access_privacy_request.manual_task_instances
        assert len(instances) == 1
        assert instances[0].id == existing_instance.id

    def test_cleanup_manual_task_instances(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test cleaning up manual task instances"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Create instances to clean up
        instance1 = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )
        instance2 = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # Verify instances exist
        assert len(access_privacy_request.manual_task_instances) == 2

        # Clean up instances
        manual_task_graph_task._cleanup_manual_task_instances(
            manual_task, access_privacy_request
        )

        # Verify instances were removed
        db.refresh(access_privacy_request)
        assert len(access_privacy_request.manual_task_instances) == 0

    def test_ensure_manual_task_instances_no_config(
        self, manual_task_graph_task, manual_task, access_privacy_request
    ):
        """Test ensuring manual task instances when no config exists"""
        # Clear configs
        manual_task.configs = []

        # This should not create any instances
        manual_task_graph_task._ensure_manual_task_instances(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Verify no instances were created
        instances = access_privacy_request.manual_task_instances
        assert len(instances) == 0

    def test_get_submitted_data_no_instances(
        self, manual_task_graph_task, manual_task, access_privacy_request
    ):
        """Test getting submitted data when no instances exist"""
        result = manual_task_graph_task._get_submitted_data(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )
        assert result is None

    def test_get_submitted_data_incomplete_fields(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test getting submitted data when instances have incomplete fields"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Create instance with incomplete fields
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # Mock incomplete_fields to return True
        with patch(
            "fides.api.models.manual_task.manual_task.ManualTaskInstance.incomplete_fields",
            return_value=True,
        ):
            result = manual_task_graph_task._get_submitted_data(
                manual_task,
                access_privacy_request,
                ManualTaskConfigurationType.access_privacy_request,
            )
            assert result is None

    def test_get_submitted_data_with_conditional_data(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test getting submitted data with conditional data"""
        _, manual_task, config, field = connection_with_manual_access_task

        # Create completed instance
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # Create a submission for the field to make it complete
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "field_id": field.id,
                "instance_id": instance.id,
                "submitted_by": None,
                "data": {
                    "field_type": ManualTaskFieldType.text.value,
                    "value": "test_value",
                },
            },
        )

        # Mock incomplete_fields to return empty list (no incomplete fields)

        result = manual_task_graph_task._get_submitted_data(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
            {"conditional": "data"},
        )

        assert result is not None
        assert "conditional" in result

    def test_process_attachment_field_no_attachments(
        self, manual_task_graph_task, manual_task_submission_attachment
    ):
        """Test processing attachment field with no attachments"""
        # Clear attachments
        manual_task_submission_attachment.attachments = []

        result = manual_task_graph_task._process_attachment_field(
            manual_task_submission_attachment
        )
        assert result is None

    def test_process_attachment_field_wrong_attachment_type(
        self,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test processing attachment field with wrong attachment type"""
        # Change attachment type to not include_with_access_package
        attachment_for_access_package.attachment_type = "internal_use_only"

        result = manual_task_graph_task._process_attachment_field(
            manual_task_submission_attachment
        )
        assert result is None

    def test_get_manual_task_or_none_invalid_address(self, manual_task_graph_task):
        """Test getting manual task with invalid address"""
        with patch.object(
            manual_task_graph_task.execution_node, "address", "invalid:address"
        ):
            with pytest.raises(ValueError, match="Invalid manual task address"):
                manual_task_graph_task._get_manual_task_or_none()

    def test_run_request_no_manual_task(self, manual_task_graph_task):
        """Test running request when no manual task exists"""
        with patch.object(
            manual_task_graph_task,
            "_get_manual_task_or_none",
            autospec=True,
            return_value=None,
        ):
            result = manual_task_graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
                [],
            )
            assert result is None

    def test_run_request_no_policy_rules(self, manual_task_graph_task, manual_task):
        """Test running request when no policy rules exist"""
        with (
            patch.object(
                manual_task_graph_task,
                "_get_manual_task_or_none",
                autospec=True,
                return_value=manual_task,
            ),
            patch.object(
                manual_task_graph_task.resources.request.policy,
                "get_rules_for_action",
                autospec=True,
                return_value=[],
            ),
        ):
            result = manual_task_graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
                [],
            )
            assert result is None

    def test_run_request_conditions_not_met(
        self, manual_task_graph_task, manual_task, access_privacy_request
    ):
        """Test running request when conditional dependencies are not met"""
        mock_evaluation_result = type("MockResult", (), {"result": False})()

        with (
            patch.object(
                manual_task_graph_task,
                "_get_manual_task_or_none",
                autospec=True,
                return_value=manual_task,
            ),
            patch.object(
                manual_task_graph_task.resources, "request", access_privacy_request
            ),
            patch.object(
                manual_task_graph_task.resources.request.policy,
                "get_rules_for_action",
                autospec=True,
                return_value=["rule"],
            ),
            patch.object(
                manual_task_graph_task,
                "_check_manual_task_configs",
                autospec=True,
                return_value=True,
            ),
            patch.object(
                manual_task_graph_task,
                "_get_conditional_data_and_evaluate",
                autospec=True,
                return_value=({}, mock_evaluation_result),
            ),
            patch.object(
                manual_task_graph_task, "_cleanup_manual_task_instances", autospec=True
            ) as mock_cleanup,
        ):
            result = manual_task_graph_task._run_request(
                ManualTaskConfigurationType.access_privacy_request,
                ActionType.access,
                [],
            )
            assert result is None
            # Verify cleanup was called with correct parameters
            mock_cleanup.assert_called_once_with(manual_task, access_privacy_request)

    def test_access_request_returns_empty_when_none(self, manual_task_graph_task):
        """Test access request returns empty list when _run_request returns None"""
        with patch.object(
            manual_task_graph_task, "_run_request", autospec=True, return_value=None
        ):
            result = manual_task_graph_task.access_request([])
            assert result == []

    def test_access_request_logs_end_when_successful(self, manual_task_graph_task):
        """Test access request logs end when successful"""
        test_data = [{"test": "data"}]

        with (
            patch.object(
                manual_task_graph_task,
                "_run_request",
                autospec=True,
                return_value=test_data,
            ),
            patch.object(
                manual_task_graph_task, "log_end", autospec=True
            ) as mock_log_end,
        ):
            result = manual_task_graph_task.access_request([])
            assert result == test_data
            mock_log_end.assert_called_once_with(ActionType.access, record_count=1)

    def test_erasure_request_no_inputs(self, manual_task_graph_task):
        """Test erasure request with no inputs"""
        with patch.object(
            manual_task_graph_task, "_run_request", autospec=True, return_value=None
        ):
            result = manual_task_graph_task.erasure_request([], inputs=[])
            assert result == 0

    def test_erasure_request_logs_end_when_successful(self, manual_task_graph_task):
        """Test erasure request logs end when successful"""
        with (
            patch.object(
                manual_task_graph_task,
                "_run_request",
                autospec=True,
                return_value=[{"test": "data"}],
            ),
            patch.object(
                manual_task_graph_task, "log_end", autospec=True
            ) as mock_log_end,
        ):
            result = manual_task_graph_task.erasure_request(
                [], inputs=[[{"test": "data"}]]
            )
            assert result == 0
            mock_log_end.assert_called_once_with(ActionType.erasure, record_count=0)

    def test_cleanup_manual_task_instances_no_instances(
        self, manual_task_graph_task, manual_task, access_privacy_request
    ):
        """Test cleaning up manual task instances when none exist"""
        # Verify no instances exist
        assert len(access_privacy_request.manual_task_instances) == 0

        # This should not raise any errors
        manual_task_graph_task._cleanup_manual_task_instances(
            manual_task, access_privacy_request
        )

        # Still no instances
        assert len(access_privacy_request.manual_task_instances) == 0

    def test_set_submitted_data_or_raise_awaiting_async_task_callback_no_submitted_data(
        self, manual_task_graph_task, manual_task, access_privacy_request, db
    ):
        """Test the else branch when submitted_data is None"""
        with (
            patch.object(
                manual_task_graph_task,
                "_get_submitted_data",
                autospec=True,
                return_value=None,
            ),
            patch.object(
                manual_task_graph_task.resources.request, "save", autospec=True
            ),
        ):
            # This should raise AwaitingAsyncTaskCallback
            with pytest.raises(
                AwaitingAsyncTaskCallback,
                match="Manual task for .* requires user input",
            ):
                manual_task_graph_task._set_submitted_data_or_raise_awaiting_async_task_callback(
                    manual_task,
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                )

    def test_set_submitted_data_or_raise_awaiting_async_task_callback_with_awaiting_message(
        self, manual_task_graph_task, manual_task, access_privacy_request, db
    ):
        """Test the else branch when submitted_data is None and awaiting_detail_message is provided"""
        with (
            patch.object(
                manual_task_graph_task,
                "_get_submitted_data",
                autospec=True,
                return_value=None,
            ),
            patch.object(
                manual_task_graph_task.resources.request, "save", autospec=True
            ),
        ):
            # This should raise AwaitingAsyncTaskCallback with the detail message
            with pytest.raises(
                AwaitingAsyncTaskCallback,
                match="Manual task for .* requires user input. Test detail",
            ):
                manual_task_graph_task._set_submitted_data_or_raise_awaiting_async_task_callback(
                    manual_task,
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                    awaiting_detail_message="Test detail",
                )

    def test_ensure_manual_task_instances_with_config(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test creating manual task instances when config exists"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Ensure config is current and has the right type
        config.is_current = True
        config.config_type = ManualTaskConfigurationType.access_privacy_request

        manual_task_graph_task._ensure_manual_task_instances(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Verify instance was created
        instances = access_privacy_request.manual_task_instances
        assert len(instances) == 1
        assert instances[0].task_id == manual_task.id
        assert instances[0].config_id == config.id

    def test_get_submitted_data_status_update(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test status update when instances are completed"""
        _, manual_task, config, field = connection_with_manual_access_task

        # Create instance with pending status
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # Create a submission to make the instance complete
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "field_id": field.id,
                "instance_id": instance.id,
                "submitted_by": None,
                "data": {
                    "field_type": ManualTaskFieldType.text.value,
                    "value": "test_value",
                },
            },
        )

        # Mock incomplete_fields to return empty list (no incomplete fields)
        result = manual_task_graph_task._get_submitted_data(
            manual_task,
            access_privacy_request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Should return the aggregated data
        assert result is not None
        assert "user_email" in result

        # Verify status was updated to completed
        db.refresh(instance)
        assert instance.status == "completed"

    def test_run_request_with_evaluation_result(
        self, manual_task_graph_task, manual_task, access_privacy_request
    ):
        """Test _run_request when evaluation_result exists"""
        mock_evaluation_result = type("MockResult", (), {"result": True})()

        with (
            patch.object(
                manual_task_graph_task,
                "_get_manual_task_or_none",
                autospec=True,
                return_value=manual_task,
            ),
            patch.object(
                manual_task_graph_task.resources.request.policy,
                "get_rules_for_action",
                autospec=True,
                return_value=["rule"],
            ),
            patch.object(
                manual_task_graph_task,
                "_check_manual_task_configs",
                autospec=True,
                return_value=True,
            ),
            patch.object(
                manual_task_graph_task,
                "_get_conditional_data_and_evaluate",
                autospec=True,
                return_value=({"test": "data"}, mock_evaluation_result),
            ),
            patch.object(
                manual_task_graph_task, "_ensure_manual_task_instances", autospec=True
            ),
            patch.object(
                manual_task_graph_task,
                "_set_submitted_data_or_raise_awaiting_async_task_callback",
                autospec=True,
            ) as mock_set_data,
        ):
            # Mock format_evaluation_success_message
            with patch(
                "fides.api.task.manual.manual_task_graph_task.format_evaluation_success_message",
                return_value="Success message",
            ):
                mock_set_data.return_value = [{"result": "data"}]

                result = manual_task_graph_task._run_request(
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                    [],
                )

                # Should call _set_submitted_data_or_raise_awaiting_async_task_callback with detailed message
                mock_set_data.assert_called_once_with(
                    manual_task,
                    ManualTaskConfigurationType.access_privacy_request,
                    ActionType.access,
                    conditional_data={"test": "data"},
                    awaiting_detail_message="Success message",
                )

    def test_cleanup_manual_task_instances_with_instances(
        self,
        manual_task_graph_task,
        connection_with_manual_access_task,
        access_privacy_request,
        db,
    ):
        """Test cleanup when instances exist"""
        _, manual_task, config, _ = connection_with_manual_access_task

        # Create instances to clean up
        instance1 = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )
        instance2 = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

        # Verify instances exist
        assert len(access_privacy_request.manual_task_instances) == 2

        # Clean up instances
        manual_task_graph_task._cleanup_manual_task_instances(
            manual_task, access_privacy_request
        )

        # Verify instances were removed
        db.refresh(access_privacy_request)
        assert len(access_privacy_request.manual_task_instances) == 0

    def test_no_double_event_log_entries_after_submission(
        self, manual_task_graph_task, complete_manual_task_setup
    ):
        """Test that log_end is called exactly once for both access and erasure requests using real fixtures"""
        setup = complete_manual_task_setup
        manual_task = setup["manual_task"]

        # Mock _run_request to return data (simulating completed task)
        with (
            patch.object(
                manual_task_graph_task,
                "_run_request",
                autospec=True,
                return_value=[{"test": "data"}],
            ),
            patch.object(
                manual_task_graph_task, "log_end", autospec=True
            ) as mock_log_end,
        ):

            # Test access request with mocked completion
            result = manual_task_graph_task.access_request([])

            # Should return data and call log_end exactly once
            assert result is not None
            assert len(result) > 0
            mock_log_end.assert_called_once_with(
                ActionType.access, record_count=len(result)
            )
            assert mock_log_end.call_count == 1

    def test_no_double_event_log_entries_for_erasure(self, build_erasure_graph_task):
        """Test that log_end is called exactly once for erasure requests using real fixtures"""
        _, manual_task_graph_task = build_erasure_graph_task

        # Mock _run_request to return data (simulating completed task)
        with (
            patch.object(
                manual_task_graph_task,
                "_run_request",
                autospec=True,
                return_value=[{"test": "data"}],
            ),
            patch.object(
                manual_task_graph_task, "log_end", autospec=True
            ) as mock_log_end,
        ):

            # Test erasure request with mocked completion
            result = manual_task_graph_task.erasure_request(
                [], inputs=[[{"test": "data"}]]
            )

            # Should return 0 and call log_end exactly once
            assert result == 0
            mock_log_end.assert_called_once_with(ActionType.erasure, record_count=0)
            assert mock_log_end.call_count == 1

    @pytest.mark.usefixtures("complete_manual_task_setup")
    def test_no_double_event_log_entries_when_awaiting_input(
        self, manual_task_graph_task
    ):
        """Test that log_end is not called when awaiting user input using real fixtures"""
        # Mock _run_request to return None (simulating awaiting input)
        with (
            patch.object(
                manual_task_graph_task, "_run_request", autospec=True, return_value=None
            ),
            patch.object(
                manual_task_graph_task, "log_end", autospec=True
            ) as mock_log_end,
        ):

            # Test access request - should not call log_end when awaiting input
            result = manual_task_graph_task.access_request([])
            assert result == []
            mock_log_end.assert_not_called()

        # Test erasure request - should not call log_end when awaiting input
        with (
            patch.object(
                manual_task_graph_task, "_run_request", autospec=True, return_value=None
            ),
            patch.object(
                manual_task_graph_task, "log_end", autospec=True
            ) as mock_log_end,
        ):

            result = manual_task_graph_task.erasure_request([], inputs=[])
            assert result == 0
            mock_log_end.assert_not_called()

    def test_no_double_event_log_entries_with_conditional_dependencies(
        self, manual_task_graph_task
    ):
        """Test that log_end is called exactly once even with conditional dependencies"""
        # Mock the conditional dependency evaluation to return success
        with (
            patch.object(
                manual_task_graph_task,
                "_get_conditional_data_and_evaluate",
                autospec=True,
            ) as mock_evaluate,
            patch.object(
                manual_task_graph_task,
                "_run_request",
                autospec=True,
                return_value=[{"test": "data"}],
            ),
            patch.object(
                manual_task_graph_task, "log_end", autospec=True
            ) as mock_log_end,
        ):

            # Mock evaluation result
            mock_evaluation_result = type("MockResult", (), {"result": True})()
            mock_evaluate.return_value = ({"test": "data"}, mock_evaluation_result)

            # Test access request with conditional dependencies
            result = manual_task_graph_task.access_request([])

            # Should call log_end exactly once
            assert result is not None
            mock_log_end.assert_called_once_with(ActionType.access, record_count=1)
            assert mock_log_end.call_count == 1

    @pytest.mark.usefixtures("complete_manual_task_setup")
    def test_no_double_event_log_entries_in_real_awaiting_scenario(
        self, manual_task_graph_task
    ):
        """Test that log_end is not called when manual task is actually awaiting input (real scenario)"""
        with patch.object(
            manual_task_graph_task, "log_end", autospec=True
        ) as mock_log_end:
            # The retry decorator will catch AwaitingAsyncTaskCallback and return None
            # This simulates the real scenario where the task is paused awaiting input
            result = manual_task_graph_task.access_request([])

            # Should return None (from retry decorator) when awaiting input
            assert result is None

            # Verify log_end was never called
            mock_log_end.assert_not_called()
