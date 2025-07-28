from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import AwaitingAsyncTaskCallback
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
    ManualTaskConditionalDependencyType,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.graph_task import GraphTask, retry
from fides.api.task.manual.manual_task_address import ManualTaskAddress
from fides.api.task.manual.manual_task_utils import (
    get_manual_task_for_connection_config,
)
from fides.api.util.collection_util import Row
from fides.api.util.storage_util import format_size


class ManualTaskGraphTask(GraphTask):
    """GraphTask implementation for ManualTask execution"""

    def _extract_conditional_dependency_data_from_inputs(
        self, *inputs: list[Row], manual_tasks: list[ManualTask]
    ) -> dict[str, Any]:
        """
        Extract data for conditional dependency field addresses from input data.

        This method processes data from upstream regular tasks that provide fields
        referenced in manual task conditional dependencies. It extracts the relevant
        field values and makes them available for conditional dependency evaluation.

        Args:
            *inputs: Input data from upstream nodes (regular tasks)
            manual_tasks: List of manual tasks to extract conditional dependencies from

        Returns:
            Dictionary mapping field addresses to their values from input data
        """
        conditional_data: dict[str, Any] = {}

        # Get all field addresses from conditional dependencies
        field_addresses: set[str] = set()
        for manual_task in manual_tasks:
            conditional_dependencies = (
                self.resources.session.query(ManualTaskConditionalDependency)
                .filter(
                    ManualTaskConditionalDependency.manual_task_id == manual_task.id
                )
                .all()
            )

            for dependency in conditional_dependencies:
                if (
                    dependency.condition_type
                    == ManualTaskConditionalDependencyType.leaf
                ):
                    if dependency.field_address:
                        field_addresses.add(dependency.field_address)
                elif (
                    dependency.condition_type
                    == ManualTaskConditionalDependencyType.group
                ):
                    self._extract_field_addresses_from_group_recursive(
                        dependency, field_addresses
                    )

        # Extract values from input data for each field address and create nested structure
        for field_address in field_addresses:
            value = self._extract_value_from_inputs(field_address, *inputs)
            if value is not None:
                # Create nested structure that ConditionEvaluator expects
                # e.g., "user.profile.age" -> {"user": {"profile": {"age": value}}}
                self._set_nested_value(
                    conditional_data, field_address.split("."), value
                )
                logger.info(
                    "Extracted conditional dependency data: {} = {}",
                    field_address,
                    value,
                )

        return conditional_data

    def _extract_field_addresses_from_group_recursive(
        self,
        group_dependency: ManualTaskConditionalDependency,
        field_addresses: set[str],
    ) -> None:
        """Recursively extract field addresses from group conditional dependencies."""
        for child in group_dependency.children:  # type: ignore[attr-defined]
            if child.condition_type == ManualTaskConditionalDependencyType.leaf:
                if child.field_address:
                    field_addresses.add(child.field_address)
            elif child.condition_type == ManualTaskConditionalDependencyType.group:
                self._extract_field_addresses_from_group_recursive(
                    child, field_addresses
                )

    def _extract_value_from_inputs(self, field_address: str, *inputs: list[Row]) -> Any:
        """
        Extract a value for a specific field address from input data.

        This method searches through all input data from upstream regular tasks
        to find values for fields referenced in conditional dependencies.

        Args:
            field_address: The field address to extract (e.g., "user.age")
            *inputs: Input data from upstream nodes

        Returns:
            The value for the field address, or None if not found
        """
        # Parse the field address to get the path components
        path_components = field_address.split(".")

        # Search through all input data for the field
        for input_data in inputs:
            for row in input_data:
                if isinstance(row, dict):
                    value = self._get_nested_value(row, path_components)
                    if value is not None:
                        logger.debug(
                            "Found value {} for field address {} in input data",
                            value,
                            field_address,
                        )
                        return value

        logger.debug("No value found for field address {} in input data", field_address)
        return None

    def _get_nested_value(
        self, data: dict[str, Any], path_components: list[str]
    ) -> Any:
        """
        Get a nested value from a dictionary using path components.

        Args:
            data: The dictionary to search
            path_components: List of keys to traverse

        Returns:
            The value at the specified path, or None if not found
        """
        current = data
        for component in path_components:
            if isinstance(current, dict) and component in current:
                current = current[component]
            else:
                return None
        return current

    def _set_nested_value(
        self, data: dict[str, Any], path_components: list[str], value: Any
    ) -> None:
        """
        Set a nested value in a dictionary using path components.

        Args:
            data: The dictionary to modify
            path_components: List of keys to traverse
            value: The value to set
        """
        current = data
        for _, component in enumerate(path_components[:-1]):
            if component not in current:
                current[component] = {}
            current = current[component]
        current[path_components[-1]] = value

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
        from fides.api.task.conditional_dependencies.evaluator import ConditionEvaluator

        # Get the root condition for this manual task
        root_condition = ManualTaskConditionalDependency.get_root_condition(
            self.resources.session, manual_task.id
        )

        if not root_condition:
            # No conditional dependencies - always execute
            return True

        # Evaluate the condition using the data from regular tasks
        evaluator = ConditionEvaluator(self.resources.session)
        return evaluator.evaluate_rule(root_condition, conditional_data)

    @retry(action_type=ActionType.access, default_return=[])
    def access_request(self, *inputs: list[Row]) -> list[Row]:
        """
        Execute manual task logic following the standard GraphTask pattern:
        1. Create ManualTaskInstances if they don't exist
        2. Check for submissions
        3. Return data if submitted, raise AwaitingAsyncTaskCallback if not
        """
        db = self.resources.session
        collection_address = self.execution_node.address

        # Verify this is a manual task address
        if not ManualTaskAddress.is_manual_task_address(collection_address):
            raise ValueError(f"Invalid manual task address: {collection_address}")

        connection_key = ManualTaskAddress.get_connection_key(collection_address)

        # Get the manual task for this connection config (1:1 relationship)
        manual_task = get_manual_task_for_connection_config(db, connection_key)

        if not manual_task:
            return []

        # Extract conditional dependency data from inputs
        conditional_data = self._extract_conditional_dependency_data_from_inputs(
            *inputs, manual_tasks=[manual_task]
        )

        # Log the conditional data for debugging
        if conditional_data:
            logger.info(
                "Extracted conditional dependency data for manual tasks: {}",
                conditional_data,
            )

        # Filter manual tasks based on conditional dependencies
        should_execute = self._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        if not should_execute:
            logger.info(
                "No manual tasks are eligible for execution based on conditional dependencies"
            )
            self.log_end(ActionType.access)
            return []

        logger.info(
            "Manual task {} is not eligible for execution based on conditional dependencies",
            manual_task.id,
        )

        # Check if any eligible manual tasks have ACCESS configs
        has_access_configs = [
            config
            for config in manual_task.configs
            if config.is_current
            and config.config_type == ManualTaskConfigurationType.access_privacy_request
        ]

        if not has_access_configs:
            # No access configs - complete immediately
            self.log_end(ActionType.access)
            return []

        if not self.resources.request.policy.get_rules_for_action(
            action_type=ActionType.access
        ):
            # TODO: This will be changed with Manual Task Dependencies Implementation.
            self.log_end(ActionType.access)
            return []

        # Check/create manual task instances for ACCESS configs only
        self._ensure_manual_task_instances(
            db,
            manual_task,
            self.resources.request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Check if all manual task instances have submissions for ACCESS configs only
        submitted_data = self._get_submitted_data(
            db,
            manual_task,
            self.resources.request,
            ManualTaskConfigurationType.access_privacy_request,
            conditional_data=conditional_data,
        )

        if submitted_data is not None:
            result: list[Row] = [submitted_data] if submitted_data else []
            self.request_task.access_data = result

            # Mark request task as complete and write execution log
            self.log_end(ActionType.access)
            return result

        # Set privacy request status to requires_input if not already set
        if self.resources.request.status != PrivacyRequestStatus.requires_input:
            self.resources.request.status = PrivacyRequestStatus.requires_input
            self.resources.request.save(db)

        # This should trigger log_awaiting_processing via the @retry decorator
        raise AwaitingAsyncTaskCallback(
            f"Manual task for {connection_key} requires user input"
        )

    def _ensure_manual_task_instances(
        self,
        db: Session,
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
        config = next(
            (
                config
                for config in manual_task.configs
                if config.is_current and config.config_type == allowed_config_type
            ),
            None,
        )
        if config:
            ManualTaskInstance.create(
                db=db,
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
        db: Session,
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
                inst.save(db)

        # Aggregate submission data from all instances
        aggregated_data = self._aggregate_submission_data(candidate_instances)

        # Merge conditional data with aggregated submission data
        if conditional_data:
            aggregated_data.update(conditional_data)

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

        for attachment in submission.attachments or []:
            if attachment.attachment_type == AttachmentType.include_with_access_package:
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
        return 1  # Placeholder - manual tasks generate variable data

    # Provide erasure support for manual tasks
    @retry(action_type=ActionType.erasure, default_return=0)
    def erasure_request(
        self,
        retrieved_data: list[Row],
        *erasure_prereqs: int,  # noqa: D401, pylint: disable=unused-argument
        inputs: Optional[list[list[Row]]] = None,
    ) -> int:
        """Execute manual-task-driven erasure logic.

        Mirrors access_request behaviour but returns the number of rows masked (always 0)
        once all required manual task submissions are present. If submissions are
        incomplete the privacy request is paused awaiting user input.
        """
        db = self.resources.session
        collection_address = self.execution_node.address

        # Validate manual task address
        if not ManualTaskAddress.is_manual_task_address(collection_address):
            raise ValueError(f"Invalid manual task address: {collection_address}")

        connection_key = ManualTaskAddress.get_connection_key(collection_address)

        # Get the manual task for this connection config (1:1 relationship)
        manual_task = get_manual_task_for_connection_config(db, connection_key)

        if not manual_task:
            # No manual tasks defined – nothing to erase
            self.log_end(ActionType.erasure)
            return 0

        # Extract conditional dependency data from inputs
        conditional_data: dict[str, Any] = {}
        if inputs:
            conditional_data = self._extract_conditional_dependency_data_from_inputs(
                *inputs, manual_tasks=[manual_task]
            )

            # Log the conditional data for debugging
            if conditional_data:
                logger.info(
                    "Extracted conditional dependency data for manual erasure tasks: {}",
                    conditional_data,
                )

        # Filter manual tasks based on conditional dependencies
        should_execute = self._evaluate_conditional_dependencies(
            manual_task, conditional_data
        )
        if not should_execute:
            logger.info(
                "No manual tasks are eligible for erasure based on conditional dependencies"
            )
            self.log_end(ActionType.erasure)
            return 0

        logger.info(
            "Manual task {} is not eligible for erasure based on conditional dependencies",
            manual_task.id,
        )

        # Check if any eligible manual tasks have ERASURE configs
        has_erasure_configs = [
            config
            for config in manual_task.configs
            if config.is_current
            and config.config_type
            == ManualTaskConfigurationType.erasure_privacy_request
        ]

        if not has_erasure_configs:
            # No erasure configs - complete immediately
            self.log_end(ActionType.erasure)
            return 0

        # Create ManualTaskInstances for ERASURE configs only
        self._ensure_manual_task_instances(
            db,
            manual_task,
            self.resources.request,
            ManualTaskConfigurationType.erasure_privacy_request,
        )

        # Check for full submissions – reuse helper used by access flow, filtering ERASURE configs
        submissions_complete = self._get_submitted_data(
            db,
            manual_task,
            self.resources.request,
            ManualTaskConfigurationType.erasure_privacy_request,
            conditional_data=conditional_data,
        )

        # If any field submissions are missing, pause processing
        if submissions_complete is None:
            if self.resources.request.status != PrivacyRequestStatus.requires_input:
                self.resources.request.status = PrivacyRequestStatus.requires_input
                self.resources.request.save(db)
            raise AwaitingAsyncTaskCallback(
                f"Manual erasure task for {connection_key} requires user input"
            )

        # Mark rows_masked = 0 (manual tasks do not mask data directly)
        if self.request_task.id:
            # Storing result for DSR 3.0; SQLAlchemy column typing triggers mypy warning
            self.request_task.rows_masked = 0  # type: ignore[assignment]

        # Mark successful completion
        self.log_end(ActionType.erasure)
        return 0
