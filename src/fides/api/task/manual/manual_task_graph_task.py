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

        if not field_addresses:
            return conditional_data

        # Add detailed logging for debugging
        logger.info(
            "Extracting conditional dependency data for manual task {} with field addresses: {}",
            manual_task.id,
            field_addresses,
        )
        logger.info(
            "Input data details: {} inputs, types: {}",
            len(inputs),
            [type(input_data) for input_data in inputs],
        )

        # For manual tasks, we need to preserve the original field names from conditional dependencies
        # Instead of using pre_process_input_data which consolidates fields, we'll extract directly
        # from the raw input data based on the execution node's input_keys

        # Map each input to its corresponding collection address
        input_collections = self.execution_node.input_keys

        logger.info(
            "Input collections: {}, field addresses to extract: {}",
            [str(addr) for addr in input_collections],
            field_addresses,
        )

        # Extract data for each conditional dependency field address
        for field_address in field_addresses:
            field_address_obj = FieldAddress.from_string(field_address)
            source_collection = field_address_obj.collection_address()

            logger.info(
                "Looking for field '{}' from collection '{}'",
                field_address,
                source_collection,
            )

            # Find the input data for this collection
            field_value = None
            for i, input_collection in enumerate(input_collections):
                if input_collection == source_collection and i < len(inputs):
                    input_data = inputs[i]
                    if input_data:
                        # Extract the specific field from this collection's data
                        field_name = field_address_obj.field_path.levels[-1] if field_address_obj.field_path.levels else "id"

                        logger.info(
                            "Searching for field '{}' in collection '{}' data: {}",
                            field_name,
                            source_collection,
                            input_data[:2] if input_data else "empty",
                        )

                        # Look for the field in the input data
                        for row in input_data:
                            if isinstance(row, dict) and field_name in row:
                                field_value = row[field_name]
                                logger.info(
                                    "Found field '{}' = {} in row: {}",
                                    field_name,
                                    field_value,
                                    row,
                                )
                                break
                        if field_value is not None:
                            break

            # Always include the field in conditional_data, even if value is None
            # This allows conditional dependencies to evaluate existence, non-existence, and falsy values
            nested_data = self._set_nested_value(field_address, field_value)
            conditional_data = deep_update(conditional_data, nested_data)

            logger.info(
                "Extracted conditional dependency data: {} = {}",
                field_address,
                field_value,
            )

        logger.info(
            "Final conditional data extracted: {}",
            conditional_data,
        )

        return conditional_data

    def _set_nested_value(self, field_address: str, value: Any) -> dict[str, Any]:
        """
        Clean and readable approach for building nested dictionaries.

        Args:
            field_address: Dot-separated field address (e.g., "user.profile.age")
            value: The value to set

        Returns:
            Dictionary with the nested structure containing the value
        """
        parts = field_address.split(".")
        result = value

        # Build nested structure from innermost to outermost
        for part in reversed(parts):
            result = {part: result}

        return result

    def _evaluate_conditional_dependencies(
        self, manual_task: ManualTask, conditional_data: dict[str, Any]
    ) -> bool:
        """
        Evaluate conditional dependencies for a manual task using data from regular tasks.

        This method evaluates whether a manual task should be executed based on its
        conditional dependencies and the data received from upstream regular tasks.

        Args:
            manual_task: The manual task to evaluate
            conditional_data: Data from regular tasks for conditional dependency fields

        Returns:
            True if the manual task should be executed, False otherwise
        """
        # Get the root condition for this manual task
        root_condition = ManualTaskConditionalDependency.get_root_condition(
            self.resources.session, manual_task.id
        )

        if not root_condition:
            # No conditional dependencies - always execute
            logger.info(
                "No conditional dependencies found for manual task {}, executing",
                manual_task.id,
            )
            return True

        logger.info(
            "Evaluating conditional dependencies for manual task {} with data: {}",
            manual_task.id,
            conditional_data,
        )

        # Evaluate the condition using the data from regular tasks
        evaluator = ConditionEvaluator(self.resources.session)
        result = evaluator.evaluate_rule(root_condition, conditional_data)

        logger.info(
            "Conditional dependency evaluation result for manual task {}: {}",
            manual_task.id,
            result,
        )

        return result

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

    def _get_conditional_data_and_evaluate(
        self, manual_task: ManualTask, *inputs: list[Row]
    ) -> Optional[dict[str, Any]]:
        # Extract conditional dependency data from inputs
        conditional_data = self._extract_conditional_dependency_data_from_inputs(
            *inputs, manual_task=manual_task
        )

        # Log the conditional data for debugging
        logger.info(
            "Extracted conditional dependency data for manual task {}: {}",
            manual_task.id,
            conditional_data,
        )

        # Filter manual tasks based on conditional dependencies
        should_execute = self._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        if not should_execute:
            logger.info(
                "Manual task {} is not eligible for execution based on conditional dependencies",
                manual_task.id,
            )
            return None

        logger.info(
            "Manual task {} is eligible for execution based on conditional dependencies",
            manual_task.id,
        )

        return conditional_data

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

    def dry_run_task(self) -> int:
        """Return estimated row count for dry run - manual tasks don't have predictable counts"""
        return self.DRY_RUN_PLACEHOLDER_VALUE

    def _run_request(
        self,
        config_type: ManualTaskConfigurationType,
        action_type: ActionType,
        *inputs: list[Row],
    ) -> Optional[list[Row]]:
        """
        Execute manual task logic following the standard GraphTask pattern:
        1. Create ManualTaskInstances if they don't exist
        2. Check for submissions
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

        # Log details about each input
        for i, input_data in enumerate(inputs):
            logger.info(
                "Input {}: type={}, length={}, content={}",
                i,
                type(input_data),
                len(input_data) if input_data else 0,
                input_data[:2] if input_data and len(input_data) > 0 else "empty",  # Show first 2 rows
            )

        # Log execution node details
        logger.info(
            "Execution node input_keys: {}, incoming_edges: {}",
            [str(key) for key in self.execution_node.input_keys],
            [str(edge) for edge in self.execution_node.incoming_edges],
        )

        conditional_data = self._get_conditional_data_and_evaluate(manual_task, *inputs)
        if conditional_data is None:
            return None

        # Check if any eligible manual tasks have applicable configs
        if not self._check_manual_task_configs(manual_task, config_type, action_type):
            return None

        if not self.resources.request.policy.get_rules_for_action(
            action_type=action_type
        ):
            return None

        # Check/Create manual task instances for applicable configs only
        self._ensure_manual_task_instances(
            manual_task,
            self.resources.request,
            config_type,
        )

        # Check if all manual task instances have submissions for applicable configs only
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
