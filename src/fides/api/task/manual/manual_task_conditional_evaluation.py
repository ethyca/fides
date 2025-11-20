from typing import Any, Optional

from pydantic.v1.utils import deep_update
from sqlalchemy.orm import Session

from fides.api.graph.config import CollectionAddress, FieldAddress
from fides.api.models.manual_task import ManualTask
from fides.api.models.manual_task.conditional_dependency import (
    ManualTaskConditionalDependency,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.task.conditional_dependencies.evaluator import ConditionEvaluator
from fides.api.task.conditional_dependencies.privacy_request.privacy_request_data import (
    PrivacyRequestDataTransformer,
)
from fides.api.task.conditional_dependencies.schemas import EvaluationResult
from fides.api.task.conditional_dependencies.util import extract_nested_field_value
from fides.api.util.collection_util import Row


def extract_conditional_dependency_data_from_inputs(
    *inputs: list[Row],
    manual_task: ManualTask,
    input_keys: list[CollectionAddress],
    privacy_request: PrivacyRequest,
) -> dict[str, Any]:
    """
    Extract data for conditional dependency field addresses from input data.

    This method processes data from upstream regular tasks that provide fields
    referenced in manual task conditional dependencies. It extracts the relevant
    field values and makes them available for conditional dependency evaluation.

    Args:
        *inputs: Input data from upstream nodes (regular tasks)
        manual_task: Manual task to extract conditional dependencies from

    Returns:
        Dictionary mapping field addresses to their values from input data
    """

    conditional_data: dict[str, Any] = {}

    # Get all task input conditional dependencies field addresses
    field_addresses = [
        dependency.field_address
        for dependency in manual_task.conditional_dependencies
        if dependency.field_address
        and not dependency.field_address.startswith("privacy_request.")
    ]

    # Get all privacy request conditional dependencies field addresses
    privacy_request_field_addresses = {
        dependency.field_address
        for dependency in manual_task.conditional_dependencies
        if dependency.field_address
        and dependency.field_address.startswith("privacy_request.")
    }
    # If there are any privacy request conditional dependencies field addresses,
    # transform the privacy request data into a dictionary structure for evaluation
    if privacy_request_field_addresses:
        privacy_request_data_transformer = PrivacyRequestDataTransformer(
            privacy_request
        )
        conditional_privacy_request_data = (
            privacy_request_data_transformer.to_evaluation_data(
                privacy_request_field_addresses
            )
        )
        conditional_data = {**conditional_privacy_request_data}

    # if no field addresses, return conditional data which may contain privacy request data or be empty
    # This will allow the manual task to be executed if there are no conditional dependencies
    if not field_addresses:
        return conditional_data

    # For manual tasks, we need to preserve the original field names from conditional dependencies
    # Instead of using pre_process_input_data which consolidates fields, we'll extract directly
    # from the raw input data based on the execution node's input_keys

    # Create a mapping between collections and their input data
    # Convert CollectionAddress objects to strings for consistent key types
    collection_data_map = {
        str(collection_key): input_data
        for collection_key, input_data in zip(input_keys, inputs)
    }

    # Extract data for each conditional dependency field address
    for field_address in field_addresses:
        source_collection_key, field_path = parse_field_address(field_address)

        # Find the input data for this collection
        field_value = None
        input_data = collection_data_map.get(source_collection_key)
        if input_data:

            # Look for the field in the input data
            for row in input_data:

                # Traverse the nested field path to get the actual value
                field_value = extract_nested_field_value(row, field_path)

                if field_value is not None:
                    break
            # Found the field value, break out of the inner loop (over rows)
            # but continue with the outer loop to process this field

        # Always include the field in conditional_data, even if value is None
        # This allows conditional dependencies to evaluate existence, non-existence, and falsy values
        nested_data = set_nested_value(field_address, field_value)
        conditional_data = deep_update(conditional_data, nested_data)

    return conditional_data


def parse_field_address(field_address: str) -> tuple[str, list[str]]:
    """
    Parse a field address into dataset, collection, and field path.

    For complex addresses with > 2 colons, uses manual string parsing.
    For simple addresses with ≤ 2 colons, uses FieldAddress.from_string().
    """
    if field_address.count(":") > 2:
        # Parse manually: dataset:collection:field:subfield -> dataset, collection, [field, subfield]
        dataset, collection, *field_path = field_address.split(":")
        source_collection_key = f"{dataset}:{collection}"
    else:
        # Use standard FieldAddress parsing for simple cases
        field_address_obj = FieldAddress.from_string(field_address)
        source_collection_key = str(field_address_obj.collection_address())
        field_path = list(field_address_obj.field_path.levels)
    return source_collection_key, field_path


def set_nested_value(field_address: str, value: Any) -> dict[str, Any]:
    """
    Set a field value in the conditional data structure.

    Args:
        field_address: Colon-separated field address (e.g., "dataset:collection:field" or "dataset:collection:nested:field")
        value: The value to set

    Returns:
        Dictionary with the field value set at the specified path
    """
    # For conditional dependencies, we want to set the field value directly
    # The field_address format is "dataset:collection:field" or "dataset:collection:nested:field"
    # We want to create: {dataset: {collection: {field: value}}} or {dataset: {collection: {nested: {field: value}}}}
    parts = field_address.split(":")

    if len(parts) >= 3:
        dataset, collection = parts[0], parts[1]
        # Handle nested field paths beyond the first 3 parts
        if len(parts) == 3:
            # Simple case: dataset:collection:field
            field = parts[2]
            return {dataset: {collection: {field: value}}}

        # Nested case: dataset:collection:nested:field
        # Build the nested structure from the remaining parts
        nested_structure = value
        for part in reversed(parts[2:]):
            nested_structure = {part: nested_structure}
        return {dataset: {collection: nested_structure}}

    # Fallback for unexpected formats
    return {field_address: value}


def evaluate_conditional_dependencies(
    db: Session, manual_task: ManualTask, conditional_data: dict[str, Any]
) -> Optional[EvaluationResult]:
    """
    Evaluate conditional dependencies for a manual task using data from regular tasks.

    This method evaluates whether a manual task should be executed based on its
    conditional dependencies and the data received from upstream regular tasks.

    Args:
        manual_task: The manual task to evaluate
        conditional_data: Data from regular tasks for conditional dependency fields

    Returns:
        EvaluationResult object containing detailed information about which conditions
        were met or not met, or None if no conditional dependencies exist
    """
    # Get the root condition for this manual task
    root_condition = ManualTaskConditionalDependency.get_root_condition(
        db, manual_task_id=manual_task.id
    )

    if not root_condition:
        # No conditional dependencies - always execute
        return None

    # Evaluate the condition using the data from regular tasks
    evaluator = ConditionEvaluator(db)
    return evaluator.evaluate_rule(root_condition, conditional_data)
