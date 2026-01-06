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


def _email_exists_tree():
    """Return condition tree dict for email exists condition."""
    return {
        "field_address": "postgres_example_test_dataset:customer:email",
        "operator": "exists",
        "value": None,
    }


def _city_eq_new_york_tree():
    """Return condition tree dict for city == New York condition."""
    return {
        "field_address": "postgres_example_test_dataset:address:city",
        "operator": "eq",
        "value": "New York",
    }


@pytest.fixture
def email_exists_conditional_dependency(db, manual_task):
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_tree": _email_exists_tree(),
        },
    )


@pytest.fixture
def city_eq_new_york_conditional_dependency(db, manual_task):
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_tree": _city_eq_new_york_tree(),
        },
    )


def _input_group_tree():
    """Return condition tree dict for input group (email AND city)."""
    return {
        "logical_operator": "and",
        "conditions": [_email_exists_tree(), _city_eq_new_york_tree()],
    }


@pytest.fixture
def input_group_conditional_dependency(db, manual_task):
    """Create a single dependency with the full input group condition tree."""
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_tree": _input_group_tree(),
        },
    )


@pytest.fixture
def email_and_city_conditional_dependency(db, manual_task):
    """Create a single dependency with both email and city conditions."""
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_tree": _input_group_tree(),
        },
    )


def _email_and_privacy_request_tree():
    """Return condition tree with email exists AND privacy request conditions."""
    return {
        "logical_operator": "and",
        "conditions": [
            _email_exists_tree(),
            _privacy_request_location_tree(),
            _privacy_request_access_rule_tree(),
        ],
    }


@pytest.fixture
def email_and_privacy_request_conditional_dependency(db, manual_task):
    """Create a single dependency with email and privacy request conditions."""
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_tree": _email_and_privacy_request_tree(),
        },
    )


def _privacy_request_location_tree():
    """Return condition tree dict for privacy_request.location == New York."""
    return {
        "field_address": "privacy_request.location",
        "operator": "eq",
        "value": "New York",
    }


def _privacy_request_access_rule_tree():
    """Return condition tree dict for privacy_request.policy.has_access_rule == True."""
    return {
        "field_address": "privacy_request.policy.has_access_rule",
        "operator": "eq",
        "value": True,
    }


@pytest.fixture
def privacy_request_location_dependency(db, manual_task):
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_tree": _privacy_request_location_tree(),
        },
    )


@pytest.fixture
def privacy_request_access_rule_dependency(db, manual_task):
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_tree": _privacy_request_access_rule_tree(),
        },
    )


@pytest.fixture
def privacy_request_policy_id_dependency(db, manual_task, policy):
    condition_tree = {
        "field_address": "privacy_request.policy.id",
        "operator": "eq",
        "value": policy.id,
    }
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_tree": condition_tree,
        },
    )


def _privacy_request_group_tree():
    """Return condition tree dict for privacy request group (location AND access_rule)."""
    return {
        "logical_operator": "and",
        "conditions": [
            _privacy_request_location_tree(),
            _privacy_request_access_rule_tree(),
        ],
    }


@pytest.fixture
def privacy_request_group_conditional_dependency(db, manual_task):
    """Create a single dependency with the full privacy request group condition tree."""
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_tree": _privacy_request_group_tree(),
        },
    )


def _full_group_tree():
    """Return condition tree dict for the full group (inputs AND privacy_request)."""
    return {
        "logical_operator": "and",
        "conditions": [_input_group_tree(), _privacy_request_group_tree()],
    }


@pytest.fixture
def group_conditional_dependency(db, manual_task):
    """Create a single dependency with the full condition tree."""
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_tree": _full_group_tree(),
        },
    )


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
                    },
                    "privacy_request": {
                        "location": "New York",
                        "policy": {"has_access_rule": True},
                    },
                },
                True,
                id="all_conditions_met",
            ),
            param(
                {
                    "postgres_example_test_dataset": {
                        "customer": {"id": "9"},
                        "address": {"city": "New York"},
                    },
                    "privacy_request": {
                        "location": "New York",
                        "policy": {"has_access_rule": True},
                    },
                },
                False,
                id="some_conditions_not_met",
            ),
            param(
                {
                    "postgres_example_test_dataset": {
                        "customer": {"email": "customer-3@example.com"},
                        "address": {"city": "Los Angeles"},
                    },
                    "privacy_request": {
                        "location": "Los Angeles",
                        "policy": {"has_access_rule": False},
                    },
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

    @pytest.mark.usefixtures("email_and_privacy_request_conditional_dependency")
    def test_extract_conditional_dependency_data_from_inputs_and_privacy_request(
        self, manual_task_graph_task, db, manual_task, privacy_request
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
                *inputs,
                manual_task=manual_task,
                input_keys=mock_node.input_keys,
                privacy_request=privacy_request,
            )

            # Should extract the email field data
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {
                        "email": "customer-1@example.com"  # First non-None value found
                    }
                },
                "privacy_request": {
                    "location": None,
                    "policy": {"has_access_rule": True},
                },
            }
            assert result == expected

    @pytest.mark.usefixtures("email_exists_conditional_dependency")
    def test_extract_conditional_dependency_data_from_inputs_simple_field(
        self, manual_task_graph_task, db, manual_task, privacy_request
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
                *inputs,
                manual_task=manual_task,
                input_keys=mock_node.input_keys,
                privacy_request=privacy_request,
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
        self, manual_task_graph_task, db, manual_task, privacy_request
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
            condition_tree = {
                "field_address": "postgres_example_test_dataset:customer:profile:preferences:theme",
                "operator": "eq",
                "value": "dark",
            }
            ManualTaskConditionalDependency.create(
                db=db,
                data={
                    "manual_task_id": manual_task.id,
                    "condition_tree": condition_tree,
                },
            )

            # Extract the data
            result = extract_conditional_dependency_data_from_inputs(
                *inputs,
                manual_task=manual_task,
                input_keys=mock_node.input_keys,
                privacy_request=privacy_request,
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
        self, manual_task_graph_task, db, manual_task, privacy_request
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
                *inputs,
                manual_task=manual_task,
                input_keys=mock_node.input_keys,
                privacy_request=privacy_request,
            )

            # Should include the field with None value
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"email": None}  # Field not found, so None
                }
            }
            assert result == expected

    @pytest.mark.usefixtures("email_and_city_conditional_dependency")
    def test_extract_conditional_dependency_data_from_inputs_multiple_collections(
        self, manual_task_graph_task, db, manual_task, privacy_request
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
                *inputs,
                manual_task=manual_task,
                input_keys=mock_node.input_keys,
                privacy_request=privacy_request,
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
        self, manual_task_graph_task, db, manual_task, privacy_request
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
                *inputs,
                manual_task=manual_task,
                input_keys=mock_node.input_keys,
                privacy_request=privacy_request,
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
        self, manual_task_graph_task, db, manual_task, privacy_request
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
                *inputs,
                manual_task=manual_task,
                input_keys=mock_node.input_keys,
                privacy_request=privacy_request,
            )

            # Should handle empty inputs gracefully
            expected = {
                "postgres_example_test_dataset": {
                    "customer": {"email": None}  # No data to extract
                }
            }
            assert result == expected

    def test_extract_conditional_dependency_data_from_inputs_no_conditional_dependencies(
        self, manual_task_graph_task, db, manual_task, privacy_request
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
                *inputs,
                manual_task=manual_task,
                input_keys=mock_node.input_keys,
                privacy_request=privacy_request,
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

    def test_evaluate_conditional_dependencies_no_condition_tree(self, db, manual_task):
        """Test evaluating conditional dependencies when no root condition exists"""
        with patch.object(
            ManualTaskConditionalDependency, "get_condition_tree", return_value=None
        ):
            result = evaluate_conditional_dependencies(
                db, manual_task, {"test": "data"}
            )
            assert result is None

    def test_evaluate_conditional_dependencies_with_condition_tree(
        self, db, manual_task
    ):
        """Test evaluating conditional dependencies with existing root condition"""
        mock_root_condition = "mock_condition"
        mock_evaluation_result = "mock_result"

        with (
            patch.object(
                ManualTaskConditionalDependency,
                "get_condition_tree",
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

    @pytest.mark.parametrize(
        "privacy_request_location,conditional_data,expected_result",
        [
            param(
                "US-CA",
                {"privacy_request": {"location_country": "us"}},
                True,
                id="location_country_us_california",
            ),
            param(
                "US-CO",
                {"privacy_request": {"location_country": "us"}},
                True,
                id="location_country_us_colorado",
            ),
            param(
                "FR",
                {"privacy_request": {"location_country": "us"}},
                False,
                id="location_country_france_not_us",
            ),
            param(
                "FR",
                {"privacy_request": {"location_groups": ["eea"]}},
                True,
                id="location_groups_france_in_eea",
            ),
            param(
                "US-CA",
                {"privacy_request": {"location_groups": ["eea"]}},
                False,
                id="location_groups_us_not_in_eea",
            ),
            param(
                "FR",
                {"privacy_request": {"location_regulations": ["gdpr"]}},
                True,
                id="location_regulations_france_has_gdpr",
            ),
            param(
                "US-CA",
                {"privacy_request": {"location_regulations": ["gdpr"]}},
                False,
                id="location_regulations_california_no_gdpr",
            ),
        ],
    )
    def test_extract_location_convenience_fields(
        self,
        manual_task_graph_task,
        db,
        manual_task,
        privacy_request,
        privacy_request_location,
        conditional_data,
        expected_result,
    ):
        """Test that location convenience fields are correctly extracted and match expected values."""
        privacy_request.location = privacy_request_location
        privacy_request.save(db)

        with patch.object(
            manual_task_graph_task, "execution_node", autospec=True
        ) as mock_node:
            mock_node.input_keys = []

            result = extract_conditional_dependency_data_from_inputs(
                manual_task=manual_task,
                input_keys=mock_node.input_keys,
                privacy_request=privacy_request,
            )

            # Verify the extracted location convenience fields match expected
            for field_path, expected_value in conditional_data[
                "privacy_request"
            ].items():
                if field_path in result.get("privacy_request", {}):
                    actual_value = result["privacy_request"][field_path]
                    if isinstance(expected_value, list):
                        # For list fields, check if expected items are in actual
                        if expected_result:
                            assert all(
                                item in actual_value for item in expected_value
                            ), f"Expected {expected_value} to be in {actual_value}"
                        else:
                            assert not any(
                                item in actual_value for item in expected_value
                            ), f"Expected {expected_value} not to be in {actual_value}"
                    else:
                        # For scalar fields, check equality
                        if expected_result:
                            assert (
                                actual_value == expected_value
                            ), f"Expected {field_path}={expected_value}, got {actual_value}"
                        else:
                            assert (
                                actual_value != expected_value
                            ), f"Expected {field_path}!={expected_value}, but got {actual_value}"
