from typing import Any, Optional, cast

from loguru import logger
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
from fides.api.task.conditional_dependencies.privacy_request.schemas import (
    CONSENT_UNAVAILABLE_FIELDS,
    PrivacyRequestTopLevelFields,
    get_consent_unavailable_field_message,
)
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
    EvaluationResult,
)
from fides.api.task.conditional_dependencies.util import extract_nested_field_value
from fides.api.task.manual.manual_task_utils import extract_field_addresses
from fides.api.util.collection_util import Row


def get_all_field_addresses_from_manual_task(manual_task: ManualTask) -> set[str]:
    """
    Extract all field addresses from a manual task's conditional dependencies.

    Args:
        manual_task: The manual task to extract field addresses from

    Returns:
        Set of all field addresses referenced in conditional dependencies
    """
    all_field_addresses: set[str] = set()

    for dependency in manual_task.conditional_dependencies:
        tree = dependency.condition_tree
        if isinstance(tree, dict) or tree is None:
            all_field_addresses.update(extract_field_addresses(tree))

    return all_field_addresses


def has_non_privacy_request_conditions(manual_task: ManualTask) -> bool:
    """
    Check if a manual task has any conditional dependencies that reference dataset fields.

    This can be used to validate or warn about consent manual tasks that have dataset
    field conditions, since consent DSRs don't have access data flowing between nodes.
    Dataset field conditions will be filtered out at runtime but this function can be
    used for upfront validation.

    Args:
        manual_task: The manual task to check

    Returns:
        True if any condition references a dataset field (not privacy_request.*), False otherwise
    """
    all_field_addresses = get_all_field_addresses_from_manual_task(manual_task)

    # Check if any field address does NOT start with "privacy_request."
    return any(not addr.startswith("privacy_request.") for addr in all_field_addresses)


def get_consent_unavailable_conditions(
    manual_task: ManualTask,
) -> list[tuple[str, str]]:
    """
    Get a list of conditional dependency fields that are not available for consent requests.

    This is useful for validation and providing helpful error messages when configuring
    consent manual tasks.

    Args:
        manual_task: The manual task to check

    Returns:
        List of (field_path, message) tuples for unavailable fields
    """
    all_field_addresses = get_all_field_addresses_from_manual_task(manual_task)
    unavailable: list[tuple[str, str]] = []

    for addr in all_field_addresses:
        # Check for dataset fields (non-privacy_request)
        if not addr.startswith("privacy_request."):
            unavailable.append(
                (
                    addr,
                    f"{addr} is a dataset field (not available for consent requests)",
                )
            )
        # Check for unavailable privacy_request fields
        elif addr in CONSENT_UNAVAILABLE_FIELDS:
            message = get_consent_unavailable_field_message(addr)
            if message:
                unavailable.append((addr, message))

    return unavailable


def extract_privacy_request_only_conditional_data(
    field_addresses: set[str],
    privacy_request: PrivacyRequest,
) -> dict[str, Any]:
    """
    Extract conditional dependency data from privacy request only.

    This is used for consent manual tasks which cannot use dataset field conditions
    because the consent graph doesn't have access data flowing between nodes.

    Args:
        manual_task: Manual task to extract conditional dependencies from
        privacy_request: The privacy request to extract data from

    Returns:
        Dictionary containing privacy request data for conditional dependency evaluation
    """
    # Filter to only privacy_request.* field addresses
    privacy_request_field_addresses: set[str] = set(
        address for address in field_addresses if address.startswith("privacy_request.")
    )

    conditional_privacy_request_data: dict[str, Any] = {}
    if privacy_request_field_addresses:
        conditional_privacy_request_data = PrivacyRequestDataTransformer(
            privacy_request
        ).to_evaluation_data(privacy_request_field_addresses)

    return {**conditional_privacy_request_data}


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

    Note: For manual tasks, we need to preserve the original field names from dataset
    conditional dependencies instead of using pre_process_input_data which consolidates fields.

    Args:
        *inputs: Input data from upstream nodes (regular tasks)
        manual_task: Manual task to extract conditional dependencies from

    Returns:
        Dictionary mapping field addresses to their values from input data
    """

    conditional_data: dict[str, Any] = {}
    all_field_addresses: set[str] = get_all_field_addresses_from_manual_task(
        manual_task
    )

    # If there are any privacy request conditional dependencies field addresses,
    # transform the privacy request data into a dictionary structure for evaluation
    conditional_data = extract_privacy_request_only_conditional_data(
        all_field_addresses, privacy_request
    )

    # Get dataset field addresses (exclude privacy_request addresses)
    # Convert to list for iteration
    # if no field addresses, return conditional data which may contain privacy request data or be empty
    dataset_field_addresses = list(
        addr
        for addr in all_field_addresses
        if not addr.startswith(PrivacyRequestTopLevelFields.privacy_request.value)
    )
    if not dataset_field_addresses:
        return conditional_data

    # Create a mapping between collections and their input data
    # Convert CollectionAddress objects to strings for consistent key types
    collection_data_map = {
        str(collection_key): input_data
        for collection_key, input_data in zip(input_keys, inputs)
    }

    # Extract data for each conditional dependency field address
    for field_address in dataset_field_addresses:
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


class ConsentConditionFilterResult:
    """Result of filtering conditions for consent evaluation."""

    def __init__(self) -> None:
        self.filtered_condition: Optional[Condition] = None
        self.skipped_dataset_fields: list[str] = []
        self.unavailable_privacy_request_fields: list[
            tuple[str, str]
        ] = []  # (field, message) pairs

    @property
    def has_skipped_conditions(self) -> bool:
        return len(self.skipped_dataset_fields) > 0

    @property
    def has_unavailable_fields(self) -> bool:
        return len(self.unavailable_privacy_request_fields) > 0

    def get_skip_message(self) -> str:
        """Get a human-readable message about skipped conditions."""
        if not self.skipped_dataset_fields:
            return ""
        fields = ", ".join(self.skipped_dataset_fields)
        return (
            f"Note: {len(self.skipped_dataset_fields)} condition(s) referencing dataset fields "
            f"were skipped for consent evaluation (consent requests don't have data flow): {fields}"
        )

    def get_unavailable_fields_message(self) -> str:
        """Get a human-readable message about unavailable privacy request fields."""
        if not self.unavailable_privacy_request_fields:
            return ""
        messages = [msg for _, msg in self.unavailable_privacy_request_fields]
        return (
            f"Warning: {len(self.unavailable_privacy_request_fields)} condition(s) reference "
            f"privacy request fields not available for consent: {'; '.join(messages)}"
        )


def _filter_condition_tree_for_privacy_request_only(
    condition: Condition,
    filter_result: Optional[ConsentConditionFilterResult] = None,
) -> Optional[Condition]:
    """
    Filter a condition tree to only include privacy_request.* conditions
    that are available for consent requests.

    For consent tasks:
    - Dataset field conditions are removed (consent DSRs don't have data flow)
    - Privacy request fields not captured for consent are tracked with warnings
      (e.g., due_date, location_country)

    Args:
        condition: The condition (ConditionLeaf or ConditionGroup) to filter
        filter_result: Optional result object to track what was filtered

    Returns:
        Filtered condition with only available privacy_request.* conditions,
        or None if no conditions remain after filtering
    """
    if isinstance(condition, ConditionLeaf):
        field_address = condition.field_address

        # Check if it's a privacy_request field
        if field_address.startswith("privacy_request."):
            # Check if this specific field is available for consent
            if field_address in CONSENT_UNAVAILABLE_FIELDS:
                # Track unavailable privacy request fields with helpful message
                if filter_result is not None:
                    message = get_consent_unavailable_field_message(field_address)
                    if message:
                        filter_result.unavailable_privacy_request_fields.append(
                            (field_address, message)
                        )
                return None
            # Field is available for consent
            return condition

        # Track skipped dataset field conditions
        if filter_result is not None:
            filter_result.skipped_dataset_fields.append(field_address)
        return None

    # Filter all child conditions
    filtered_conditions: list[Condition] = []
    for child in condition.conditions:
        filtered_child = _filter_condition_tree_for_privacy_request_only(
            child, filter_result
        )
        if filtered_child is not None:
            filtered_conditions.append(filtered_child)

    # If no conditions remain after filtering, return None
    if not filtered_conditions:
        return None

    # If only one condition remains, return it directly (no need for group)
    if len(filtered_conditions) == 1:
        return filtered_conditions[0]

    # Return a new group with filtered conditions
    return ConditionGroup(
        logical_operator=condition.logical_operator,
        conditions=filtered_conditions,
    )


def evaluate_conditional_dependencies(
    db: Session,
    manual_task: ManualTask,
    conditional_data: dict[str, Any],
    privacy_request_only: bool = False,
) -> Optional[EvaluationResult]:
    """
    Evaluate conditional dependencies for a manual task using data from regular tasks.

    This method evaluates whether a manual task should be executed based on its
    conditional dependencies and the data received from upstream regular tasks.

    Args:
        db: Database session
        manual_task: The manual task to evaluate
        conditional_data: Data from regular tasks for conditional dependency fields
        privacy_request_only: If True, only evaluate privacy_request.* conditions.
            Used for consent tasks which don't have data flow through datasets.
            Dataset field conditions will be filtered out and the remaining
            privacy_request.* conditions will still be evaluated.

    Returns:
        EvaluationResult object containing detailed information about which conditions
        were met or not met, or None if no conditional dependencies exist
    """
    # Note: For consent tasks (privacy_request_only=True), dataset field conditions
    # are filtered out by _filter_condition_tree_for_privacy_request_only below.
    # We don't skip evaluation entirely - we filter and evaluate what remains.

    # Get the condition tree for this manual task
    condition_tree = ManualTaskConditionalDependency.get_condition_tree(
        db, manual_task_id=manual_task.id
    )

    if not condition_tree:
        # No conditional dependencies - always execute
        return None

    # For consent tasks, filter out dataset field conditions and unavailable fields
    filter_result: Optional[ConsentConditionFilterResult] = None
    if privacy_request_only:
        filter_result = ConsentConditionFilterResult()
        condition_tree = _filter_condition_tree_for_privacy_request_only(
            condition_tree, filter_result
        )
        # Log skipped dataset conditions for visibility
        if filter_result.has_skipped_conditions:
            logger.info(filter_result.get_skip_message())

        # Warn about unavailable privacy request fields
        if filter_result.has_unavailable_fields:
            logger.warning(filter_result.get_unavailable_fields_message())

        if condition_tree is None:
            # No evaluable conditions remain - always execute
            if filter_result.has_unavailable_fields:
                logger.info(
                    "All conditions for consent manual task referenced unavailable fields "
                    "and were skipped. Task will execute unconditionally."
                )
            else:
                logger.info(
                    "All conditions for consent manual task referenced dataset fields "
                    "and were skipped. Task will execute unconditionally."
                )
            return None

    # Evaluate the condition using the data from regular tasks
    # At this point condition_tree cannot be None (early return above handles that case)
    assert condition_tree is not None
    evaluator = ConditionEvaluator(db)
    return evaluator.evaluate_rule(condition_tree, conditional_data)
