from unittest.mock import patch

import pytest
from pytest import param

from fides.api.models.manual_task.conditional_dependency import (
    ManualTaskConditionalDependency,
)
from fides.api.task.manual.manual_task_conditional_evaluation import (
    evaluate_conditional_dependencies,
    extract_conditional_dependency_data_from_inputs,
    extract_nested_field_value,
    parse_field_address,
    set_nested_value,
)


@pytest.fixture
def email_exists_conditional_dependency(db, manual_task):
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
    yield dependency
    dependency.delete(db)


@pytest.fixture
def city_eq_new_york_conditional_dependency(db, manual_task):
    dependency = ManualTaskConditionalDependency.create(
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
    yield dependency
    dependency.delete(db)


@pytest.fixture
def group_conditional_dependency(
    db,
    manual_task,
    email_exists_conditional_dependency,
    city_eq_new_york_conditional_dependency,
):
    dependency = ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": "group",
            "logical_operator": "and",
            "sort_order": 1,
        },
    )

    email_exists_conditional_dependency.parent = dependency
    email_exists_conditional_dependency.sort_order = 3
    city_eq_new_york_conditional_dependency.parent = dependency
    dependency.children = [
        email_exists_conditional_dependency,
        city_eq_new_york_conditional_dependency,
    ]
    db.commit()
    yield dependency
    dependency.delete(db)


class TestManualTaskConditionalDependencies:
    """Test that Manual Tasks only create instances when conditional dependencies are met"""

    @pytest.mark.usefixtures("group_conditional_dependency")
    @pytest.mark.parametrize(
        "conditional_data, expected_evaluation_result",
        [
            param(
                {
                    "postgres_example_test_dataset": {
                        "customer": {"email": "customer-1@example.com"},
                        "address": {"city": "New York"},
                    }
                },
                True,
                id="all_conditions_met",
            ),
            param(
                {
                    "postgres_example_test_dataset": {
                        "customer": {"id": "9"},
                        "address": {"city": "New York"},
                    }
                },
                False,
                id="some_conditions_not_met",
            ),
            param(
                {
                    "postgres_example_test_dataset": {
                        "customer": {"email": "customer-3@example.com"},
                        "address": {"city": "Los Angeles"},
                    }
                },
                False,
                id="no_conditions_met",
            ),
        ],
    )
    def test_evaluate_group_conditional_dependencies(
        self, db, manual_task, conditional_data, expected_evaluation_result
    ):
        result = evaluate_conditional_dependencies(db, manual_task, conditional_data)
        assert result.result == expected_evaluation_result

    def test_evaluate_group_conditional_dependencies_no_root_condition(
        self, db, manual_task
    ):
        result = evaluate_conditional_dependencies(db, manual_task, {})
        assert result is None

    @pytest.mark.usefixtures("email_exists_conditional_dependency")
    @pytest.mark.parametrize(
        "conditional_data, expected_evaluation_result",
        [
            param(
                {
                    "postgres_example_test_dataset": {
                        "customer": {"email": "customer-1@example.com"}
                    }
                },
                True,
                id="all_conditions_met",
            ),
            param(
                {"postgres_example_test_dataset": {"customer": {"id": "9"}}},
                False,
                id="some_conditions_not_met",
            ),
        ],
    )
    def test_evaluate_group_conditional_dependencies_with_root_condition(
        self, db, manual_task, conditional_data, expected_evaluation_result
    ):
        result = evaluate_conditional_dependencies(db, manual_task, conditional_data)
        assert result.result == expected_evaluation_result


class TestManualTaskDataExtraction:
    """Test the _extract_conditional_dependency_data_from_inputs method in ManualTaskGraphTask"""

    def setup_method(self):
        """Import CollectionAddress for all test methods"""
        from fides.api.graph.config import CollectionAddress

        self.CollectionAddress = CollectionAddress

    @pytest.mark.usefixtures("email_exists_conditional_dependency")
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
            # Extract the data
            result = extract_conditional_dependency_data_from_inputs(
                *inputs, manual_task=manual_task, input_keys=mock_node.input_keys
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
            ManualTaskConditionalDependency.create(
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
            result = extract_conditional_dependency_data_from_inputs(
                *inputs, manual_task=manual_task, input_keys=mock_node.input_keys
            )

            # Should extract the nested field data
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"profile": {"preferences": {"theme": "dark"}}}
                }
            }
            assert result == expected

    @pytest.mark.usefixtures("email_exists_conditional_dependency")
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

            # Extract the data
            result = extract_conditional_dependency_data_from_inputs(
                *inputs, manual_task=manual_task, input_keys=mock_node.input_keys
            )

            # Should include the field with None value
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"email": None}  # Field not found, so None
                }
            }
            assert result == expected

    @pytest.mark.usefixtures(
        "email_exists_conditional_dependency", "city_eq_new_york_conditional_dependency"
    )
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

            # Extract the data
            result = extract_conditional_dependency_data_from_inputs(
                *inputs, manual_task=manual_task, input_keys=mock_node.input_keys
            )

            # Should extract data from both collections
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"email": "customer-1@example.com"},
                    "address": {"city": "New York"},
                }
            }
            assert result == expected

    @pytest.mark.usefixtures("email_exists_conditional_dependency")
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

            # Extract the data
            result = extract_conditional_dependency_data_from_inputs(
                *inputs, manual_task=manual_task, input_keys=mock_node.input_keys
            )

            # Should correctly parse the field address and extract the data
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"email": "customer-1@example.com"}
                }
            }
            assert result == expected

    @pytest.mark.usefixtures("email_exists_conditional_dependency")
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

            # Extract the data
            result = extract_conditional_dependency_data_from_inputs(
                *inputs, manual_task=manual_task, input_keys=mock_node.input_keys
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
            result = extract_conditional_dependency_data_from_inputs(
                *inputs, manual_task=manual_task, input_keys=mock_node.input_keys
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
        field_address,
        expected_source_collection_key,
        expected_field_path,
    ):
        """Test parsing field addresses with various formats and edge cases"""
        source_collection_key, field_path = parse_field_address(field_address)

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
    def test_extract_nested_field_value(self, data, field_path, expected_result):
        """Test extracting nested field value with empty field path"""
        result = extract_nested_field_value(data, field_path)
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
    def test_set_nested_value(self, field_address, expected_result):
        """Test setting nested value for simple 3-part field address"""
        value = "test_value"
        result = set_nested_value(field_address, value)
        assert result == expected_result

    def test_evaluate_conditional_dependencies_no_root_condition(self, db, manual_task):
        """Test evaluating conditional dependencies when no root condition exists"""
        with patch.object(
            ManualTaskConditionalDependency, "get_root_condition", return_value=None
        ):
            result = evaluate_conditional_dependencies(
                db, manual_task, {"test": "data"}
            )
            assert result is None

    def test_evaluate_conditional_dependencies_with_root_condition(
        self, db, manual_task
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
                "fides.api.task.manual.manual_task_conditional_evaluation.ConditionEvaluator"
            ) as mock_evaluator_class,
        ):
            mock_evaluator = mock_evaluator_class.return_value
            mock_evaluator.evaluate_rule.return_value = mock_evaluation_result

            result = evaluate_conditional_dependencies(
                db, manual_task, {"test": "data"}
            )
            assert result == mock_evaluation_result
