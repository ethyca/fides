from typing import Any, Optional

from loguru import logger
from pydantic.v1.utils import deep_update

from fides.api.common_exceptions import AwaitingAsyncTaskCallback
from fides.api.graph.config import FieldAddress
from fides.api.models.attachment import AttachmentType
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfigurationType,
    ManualTaskEntityType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskSubmission,
    StatusType,
)
from fides.api.models.manual_task.conditional_dependency import (
    ManualTaskConditionalDependency,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.conditional_dependencies.evaluator import ConditionEvaluator
from fides.api.task.conditional_dependencies.logging_utils import (
    format_evaluation_failure_message,
    format_evaluation_success_message,
)
from fides.api.task.graph_task import GraphTask, retry
from fides.api.task.manual.manual_task_address import ManualTaskAddress
from fides.api.task.manual.manual_task_utils import (
    get_manual_task_for_connection_config,
)
from fides.api.task.task_resources import TaskResources
from fides.api.util.collection_util import Row
from fides.api.util.storage_util import format_size


class ManualTaskGraphTask(GraphTask):
    """GraphTask implementation for ManualTask execution"""

    # class level constants
    DRY_RUN_PLACEHOLDER_VALUE = 1

    def __init__(self, resources: TaskResources) -> None:
        super().__init__(resources)
        self.connection_key = ManualTaskAddress.get_connection_key(
            self.execution_node.address
        )

    def dry_run_task(self) -> int:
        """Return estimated row count for dry run - manual tasks don't have predictable counts"""
        return self.DRY_RUN_PLACEHOLDER_VALUE

    def _parse_field_address(self, field_address: str) -> tuple[str, list[str]]:
        """
        Parse a field address into dataset, collection, and field path.
        """
        if field_address.count(":") > 2:
            # Parse manually: dataset:collection:field:subfield -> dataset, collection, [field, subfield]
            dataset, collection, *field_path = field_address.split(":")
            source_collection_key = f"{dataset}:{collection}"
        else:
            # Use standard FieldAddress parsing for simple cases
            field_address_obj = FieldAddress.from_string(field_address)
            source_collection_key = str(field_address_obj.collection_address())
            field_path = (
                list(field_address_obj.field_path.levels)
                if field_address_obj.field_path.levels
                else ["id"]
            )
        return source_collection_key, field_path

    def _extract_conditional_dependency_data_from_inputs(
        self, *inputs: list[Row], manual_task: ManualTask
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

        # Get all conditional dependencies field addresses
        field_addresses = [
            dependency.field_address
            for dependency in manual_task.conditional_dependencies
            if dependency.field_address
        ]

        # if no field addresses, return empty conditional data
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
            for collection_key, input_data in zip(
                self.execution_node.input_keys, inputs
            )
        }

        # Extract data for each conditional dependency field address
        for field_address in field_addresses:
            source_collection_key, field_path = self._parse_field_address(field_address)

            # Find the input data for this collection
            field_value = None
            input_data = collection_data_map.get(source_collection_key)
            if input_data:

                # Look for the field in the input data
                for row in input_data:

                    # Traverse the nested field path to get the actual value
                    field_value = self._extract_nested_field_value(row, field_path)

                    if field_value is not None:
                        break
                # Found the field value, break out of the inner loop (over rows)
                # but continue with the outer loop to process this field

            # Always include the field in conditional_data, even if value is None
            # This allows conditional dependencies to evaluate existence, non-existence, and falsy values
            nested_data = self._set_nested_value(field_address, field_value)
            conditional_data = deep_update(conditional_data, nested_data)

        return conditional_data

    def _extract_nested_field_value(self, data: Any, field_path: list[str]) -> Any:
        """
        Extract a nested field value by traversing the field path.

        Args:
            data: The data to extract from (usually a dict)
            field_path: List of field names to traverse (e.g., ["profile", "preferences", "theme"])

        Returns:
            The value at the end of the field path, or None if not found
        """
        if not field_path:
            return data

        current = data
        for field_name in field_path:
            if isinstance(current, dict) and field_name in current:
                current = current[field_name]
            else:
                return None

        return current

    def _set_nested_value(self, field_address: str, value: Any) -> dict[str, Any]:
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

    def _evaluate_conditional_dependencies(
        self, manual_task: ManualTask, conditional_data: dict[str, Any]
    ) -> tuple[bool, Optional[Any]]:
        """
        Evaluate conditional dependencies for a manual task using data from regular tasks.

        This method evaluates whether a manual task should be executed based on its
        conditional dependencies and the data received from upstream regular tasks.

        Args:
            manual_task: The manual task to evaluate
            conditional_data: Data from regular tasks for conditional dependency fields

        Returns:
            Tuple of (should_execute, evaluation_result) where evaluation_result contains
            detailed information about which conditions were met or not met
        """
        # Get the root condition for this manual task
        root_condition = ManualTaskConditionalDependency.get_root_condition(
            self.resources.session, manual_task.id
        )

        if not root_condition:
            # No conditional dependencies - always execute
            return True, None

        # Evaluate the condition using the data from regular tasks
        evaluator = ConditionEvaluator(self.resources.session)
        result, evaluation_result = evaluator.evaluate_rule(
            root_condition, conditional_data
        )

        return result, evaluation_result

    def _get_conditional_data_and_evaluate(
        self, manual_task: ManualTask, *inputs: list[Row]
    ) -> tuple[Optional[dict[str, Any]], Optional[Any]]:
        # Extract conditional dependency data from inputs
        conditional_data = self._extract_conditional_dependency_data_from_inputs(
            *inputs, manual_task=manual_task
        )

        # Filter manual tasks based on conditional dependencies
        should_execute, evaluation_result = self._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        if not should_execute:
            # Create detailed message about which conditions failed
            detailed_message = format_evaluation_failure_message(evaluation_result)
            self.resources.request.add_skipped_execution_log(
                db=self.resources.session,
                connection_key=self.connection_key,
                dataset_name=None,
                collection_name=str(self.execution_node.address),
                message=f"Manual task conditional dependencies not met. {detailed_message}",
                action_type=ActionType(self.resources.privacy_request_task.action_type),
            )
            return None, evaluation_result

        return conditional_data, evaluation_result

    def _check_manual_task_configs(
        self,
        manual_task: ManualTask,
        config_type: ManualTaskConfigurationType,
        action_type: ActionType,
    ) -> bool:
        has_access_configs = [
            config
            for config in manual_task.configs
            if config.is_current and config.config_type == config_type
        ]

        if not has_access_configs:
            # No access configs - complete immediately
            self.log_end(action_type)
            return False

        return True

    def _set_submitted_data_or_raise_awaiting_async_task_callback(
        self,
        manual_task: ManualTask,
        config_type: ManualTaskConfigurationType,
        action_type: ActionType,
        conditional_data: Optional[dict[str, Any]] = None,
    ) -> Optional[list[Row]]:
        """
        Set submitted data for a manual task and raise AwaitingAsyncTaskCallback if all instances are not completed
        """
        # Check if all manual task instances have submissions for ACCESS configs only
        submitted_data = self._get_submitted_data(
            manual_task,
            self.resources.request,
            config_type,
            conditional_data=conditional_data,
        )

        if submitted_data is not None:
            result: list[Row] = [submitted_data] if submitted_data else []
            self.request_task.access_data = result

            return result

        # Set privacy request status to requires_input if not already set
        if self.resources.request.status != PrivacyRequestStatus.requires_input:
            self.resources.request.status = PrivacyRequestStatus.requires_input
            self.resources.request.save(self.resources.session)

        # This should trigger log_awaiting_processing via the @retry decorator
        raise AwaitingAsyncTaskCallback(
            f"Manual task for {self.connection_key} requires user input"
        )

    def _ensure_manual_task_instances(
        self,
        manual_task: ManualTask,
        privacy_request: PrivacyRequest,
        allowed_config_type: "ManualTaskConfigurationType",
    ) -> None:
        """Create ManualTaskInstances for configs matching `allowed_config_type` if they don't exist."""

        # ------------------------------------------------------------------
        # Check if instances already exist for this task & entity with the SAME config type
        # This prevents duplicates when configurations are versioned after the privacy
        # request has started, while allowing different config types (access vs erasure)
        # to have separate instances.
        # ------------------------------------------------------------------
        existing_task_instance = next(
            (
                instance
                for instance in privacy_request.manual_task_instances
                if instance.task_id == manual_task.id
                and instance.config.config_type == allowed_config_type
            ),
            None,
        )
        if existing_task_instance:
            # An instance already exists for this privacy request and config type – no need
            # to create another one tied to a newer config version.
            return

        # If no existing instances, create a new one for the current config
        # There will only be one config of each type per manual task
        # Sort by version descending to get the latest version first
        config = next(
            (
                config
                for config in sorted(
                    manual_task.configs,
                    key=lambda c: c.version if hasattr(c, "version") else 0,
                    reverse=True,
                )
                if config.is_current and config.config_type == allowed_config_type
            ),
            None,
        )

        if config:
            ManualTaskInstance.create(
                db=self.resources.session,
                data={
                    "task_id": manual_task.id,
                    "config_id": config.id,
                    "entity_id": privacy_request.id,
                    "entity_type": ManualTaskEntityType.privacy_request.value,
                    "status": StatusType.pending.value,
                },
            )

    def _get_submitted_data(
        self,
        manual_task: ManualTask,
        privacy_request: PrivacyRequest,
        allowed_config_type: "ManualTaskConfigurationType",
        conditional_data: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Check if all manual task instances have submissions for ALL fields and return aggregated data
        Returns None if any field submissions are missing (all fields must be completed or skipped)
        """
        candidate_instances: list[ManualTaskInstance] = [
            instance
            for instance in privacy_request.manual_task_instances
            if instance.task_id == manual_task.id
            and instance.config.config_type == allowed_config_type
        ]

        if not candidate_instances:
            return None  # No instance yet for this manual task

        # Check for incomplete fields and update status in single pass
        for inst in candidate_instances:
            if inst.incomplete_fields:
                return None  # At least one instance still incomplete

            # Update status if needed
            if inst.status != StatusType.completed:
                inst.status = StatusType.completed
                inst.save(self.resources.session)

        # Aggregate submission data from all instances
        aggregated_data = self._aggregate_submission_data(candidate_instances)

        # Merge conditional data with aggregated submission data
        if conditional_data:
            aggregated_data = deep_update(aggregated_data, conditional_data)

        return aggregated_data or None

    def _aggregate_submission_data(
        self, instances: list[ManualTaskInstance]
    ) -> dict[str, Any]:
        """Aggregate submission data from all instances into a single dictionary."""
        aggregated_data: dict[str, Any] = {}

        for inst in instances:
            # Filter valid submissions and process them
            valid_submissions = (
                submission
                for submission in inst.submissions
                if (
                    submission.field
                    and submission.field.field_key
                    and isinstance(submission.data, dict)
                )
            )

            for submission in valid_submissions:
                field_key = submission.field.field_key
                # We already checked isinstance(submission.data, dict) in valid_submissions
                data_dict: dict[str, Any] = submission.data  # type: ignore[assignment]
                field_type = data_dict.get("field_type")

                # Process field data based on type
                aggregated_data[field_key] = (
                    self._process_attachment_field(submission)
                    if field_type == ManualTaskFieldType.attachment.value
                    else data_dict.get("value")
                )

        return aggregated_data

    def _process_attachment_field(
        self, submission: ManualTaskSubmission
    ) -> Optional[dict[str, dict[str, Any]]]:
        """Process attachment field and return attachment map or None."""
        attachment_map: dict[str, dict[str, Any]] = {}

        for attachment in filter(
            lambda a: a.attachment_type == AttachmentType.include_with_access_package,
            submission.attachments,
        ):
            try:
                size, url = attachment.retrieve_attachment()
                attachment_map[attachment.file_name] = {
                    "url": str(url) if url else None,
                    "size": (format_size(size) if size else "Unknown"),
                }
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.warning(
                    f"Error retrieving attachment {attachment.file_name}: {str(exc)}"
                )
        return attachment_map or None

    def _get_manual_task_or_none(self) -> Optional[ManualTask]:
        # Verify this is a manual task address
        if not ManualTaskAddress.is_manual_task_address(self.execution_node.address):
            raise ValueError(
                f"Invalid manual task address: {self.execution_node.address}"
            )

        # Get the manual task for this connection config (1:1 relationship)
        manual_task = get_manual_task_for_connection_config(
            self.resources.session, self.connection_key
        )
        return manual_task

    def _run_request(
        self,
        config_type: ManualTaskConfigurationType,
        action_type: ActionType,
        *inputs: list[Row],
    ) -> Optional[list[Row]]:
        """
        Execute manual task logic following the standard GraphTask pattern:
        1. Create ManualTaskInstances if they don't exist
        2. Check if all required submissions are present
        3. Return data if submitted, raise AwaitingAsyncTaskCallback if not
        """
        manual_task = self._get_manual_task_or_none()
        if manual_task is None:
            return None

        # Add detailed logging to debug input data flow
        logger.info(
            "ManualTaskGraphTask._run_request called for manual task {} with {} inputs",
            manual_task.id,
            len(inputs),
        )

        # Check if any eligible manual tasks have applicable configs
        if not self._check_manual_task_configs(manual_task, config_type, action_type):
            return None

        if not self.resources.request.policy.get_rules_for_action(
            action_type=action_type
        ):
            return None

        conditional_data, evaluation_result = self._get_conditional_data_and_evaluate(
            manual_task, *inputs
        )
        if conditional_data is None:
            # Clean up any existing ManualTaskInstances for this manual task since conditions are not met
            self._cleanup_manual_task_instances(manual_task, self.resources.request)
            return None

        # Check/Create manual task instances for applicable configs only
        self._ensure_manual_task_instances(
            manual_task,
            self.resources.request,
            config_type,
        )

        # Check if all manual task instances have submissions for applicable configs only
        # Log the conditional dependency evaluation result if it exists
        if evaluation_result:
            detailed_message = format_evaluation_success_message(evaluation_result)
            self.resources.request.add_pending_execution_log(
                db=self.resources.session,
                connection_key=self.connection_key,
                dataset_name=None,
                collection_name=str(self.execution_node.address),
                message=f"Manual task conditional dependencies met. {detailed_message}",
                action_type=ActionType(self.resources.privacy_request_task.action_type),
            )
        result = self._set_submitted_data_or_raise_awaiting_async_task_callback(
            manual_task,
            config_type,
            action_type,
            conditional_data=conditional_data,
        )
        return result

    @retry(action_type=ActionType.access, default_return=[])
    def access_request(self, *inputs: list[Row]) -> list[Row]:
        """
        Execute manual task logic following the standard GraphTask pattern.
        Calls _run_request with ACCESS configs.
        Returns data if submitted, raise AwaitingAsyncTaskCallback if not
        """
        result = self._run_request(
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
            *inputs,
        )
        if result is None:
            self.log_end(ActionType.access)
            return []

        self.log_end(ActionType.access)
        return result

    # Provide erasure support for manual tasks
    @retry(action_type=ActionType.erasure, default_return=0)
    def erasure_request(
        self,
        retrieved_data: list[Row],  # This is not used for manual tasks.
        *erasure_prereqs: int,  # noqa: D401, pylint: disable=unused-argument # TODO Remove when we stop support for DSR 2.0
        inputs: Optional[list[list[Row]]] = None,
    ) -> int:
        """Execute manual-task-driven erasure logic.
        Calls _run_request with ERASURE configs.

        Mirrors access_request behaviour but returns the number of rows masked (always 0)
        once all required manual task submissions are present. If submissions are
        incomplete the privacy request is paused awaiting user input.
        Returns the number of rows masked (always 0)
        Raises AwaitingAsyncTaskCallback if data is not submitted
        """
        if not inputs:
            inputs = []
        result = self._run_request(
            ManualTaskConfigurationType.erasure_privacy_request,
            ActionType.erasure,
            *inputs,
        )
        if result is None:
            self.log_end(ActionType.erasure)
            return 0

        # Mark rows_masked = 0 (manual tasks do not mask data directly)
        if self.request_task.id:
            # Storing result for DSR 3.0; SQLAlchemy column typing triggers mypy warning
            self.request_task.rows_masked = 0  # type: ignore[assignment]

        # Mark successful completion
        self.log_end(ActionType.erasure)
        return 0

    def _cleanup_manual_task_instances(
        self, manual_task: ManualTask, privacy_request: PrivacyRequest
    ) -> None:
        """
        Clean up ManualTaskInstances for a manual task when conditional dependencies are not met.

        This method removes any existing instances that were created before the conditional
        dependency evaluation determined the task should not execute.
        """
        # Find all instances for this manual task and privacy request
        instances_to_remove = [
            instance
            for instance in privacy_request.manual_task_instances
            if instance.task_id == manual_task.id
        ]

        if instances_to_remove:
            logger.info(
                "Cleaning up {} ManualTaskInstance(s) for manual task {} since conditional dependencies are not met",
                len(instances_to_remove),
                manual_task.id,
            )

            # Remove instances from the database
            for instance in instances_to_remove:
                self.resources.session.delete(instance)

            logger.info(
                "Successfully cleaned up ManualTaskInstance(s) for manual task {}",
                manual_task.id,
            )
