from typing import Any, Optional

from loguru import logger
from pydantic.v1.utils import deep_update

from fides.api.common_exceptions import AwaitingAsyncTask
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
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.conditional_dependencies.logging_utils import (
    format_evaluation_failure_message,
    format_evaluation_success_message,
)
from fides.api.task.graph_task import GraphTask, retry
from fides.api.task.manual.manual_task_address import ManualTaskAddress
from fides.api.task.manual.manual_task_conditional_evaluation import (
    evaluate_conditional_dependencies,
    extract_conditional_dependency_data_from_inputs,
)
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

    # ------------------------------------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------------------------------------

    def dry_run_task(self) -> int:
        """Return estimated row count for dry run - manual tasks don't have predictable counts"""
        return self.DRY_RUN_PLACEHOLDER_VALUE

    @retry(action_type=ActionType.access, default_return=[])
    def access_request(self, *inputs: list[Row]) -> list[Row]:
        """
        Execute manual task logic following the standard GraphTask pattern.
        Calls _run_request with ACCESS configs.
        Returns data if submitted, raise AwaitingAsyncTaskCallback if not
        """
        if self.resources.request.policy.get_action_type() == ActionType.erasure:
            # We're in an erasure privacy request's access phase - complete access task immediately
            # since access is just for data collection to support erasure, not for user data access
            self.update_status(
                "Access task completed immediately for erasure privacy request (data collection only)",
                [],
                ActionType.access,
                ExecutionLogStatus.complete,
            )
            return []

        result = self._run_request(
            ManualTaskConfigurationType.access_privacy_request,
            ActionType.access,
            *inputs,
        )
        if result is None:
            # Conditional skip or not applicable already logged upstream; do not mark complete here
            return []

        # We are picking up after awaiting input and have provided data – mark complete with record count
        self.log_end(ActionType.access, record_count=len(result))
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
            # Conditional skip or not applicable already logged upstream; do not mark complete here
            return 0

        # Mark rows_masked = 0 (manual tasks do not mask data directly)
        if self.request_task.id:
            # Storing result for DSR 3.0; SQLAlchemy column typing triggers mypy warning
            self.request_task.rows_masked = 0  # type: ignore[assignment]

        # Picking up after awaiting input, mark erasure node complete with rows masked count (always 0)
        self.log_end(ActionType.erasure, record_count=0)
        return 0

    # ------------------------------------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------------------------------------

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
        3. Return data if submitted, raise AwaitingAsyncTask if not
        """
        manual_task = self._get_manual_task_or_none()
        if manual_task is None:
            return None

        # Complete a series of checks to determine if the manual task should be executed
        # If any of these checks fail, complete immediately or mark as skipped

        # Check if any eligible manual tasks have applicable configs
        if not self._check_manual_task_configs(manual_task, config_type, action_type):
            return None

        # Check if there are any rules for this action type
        if not self.resources.request.policy.get_rules_for_action(
            action_type=action_type
        ):
            return None

        # Extract conditional dependency data from inputs
        conditional_data = extract_conditional_dependency_data_from_inputs(
            *inputs, manual_task=manual_task, input_keys=self.execution_node.input_keys
        )
        # Evaluate conditional dependencies
        evaluation_result = evaluate_conditional_dependencies(
            self.resources.session, manual_task, conditional_data=conditional_data
        )
        detailed_message: Optional[str] = None
        # if there were conditional dependencies and they were not met,
        # clean up any existing ManualTaskInstances and return None to cause a skip
        if evaluation_result is not None and not evaluation_result.result:
            self._cleanup_manual_task_instances(manual_task, self.resources.request)
            detailed_message = format_evaluation_failure_message(evaluation_result)
            self.update_status(
                f"Manual task conditional dependencies not met. {detailed_message}",
                [],
                ActionType(self.resources.privacy_request_task.action_type),
                ExecutionLogStatus.skipped,
            )
            return None

        # Check/Create manual task instances for applicable configs only
        self._ensure_manual_task_instances(
            manual_task,
            self.resources.request,
            config_type,
        )

        # Check if all manual task instances have submissions for applicable configs only
        # No separate pending log; include details in the awaiting-processing log
        if evaluation_result:
            detailed_message = format_evaluation_success_message(evaluation_result)
        result = self._set_submitted_data_or_raise_awaiting_async_task_callback(
            manual_task,
            config_type,
            action_type,
            conditional_data=conditional_data,
            awaiting_detail_message=detailed_message,
        )
        return result

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

    def _set_submitted_data_or_raise_awaiting_async_task_callback(
        self,
        manual_task: ManualTask,
        config_type: ManualTaskConfigurationType,
        action_type: ActionType,
        conditional_data: Optional[dict[str, Any]] = None,
        awaiting_detail_message: Optional[str] = None,
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

        # This will trigger log_awaiting_processing via the @retry decorator; include conditional details
        base_msg = f"Manual task for {self.connection_key} requires user input"
        if awaiting_detail_message:
            base_msg = f"{base_msg}. {awaiting_detail_message}"
        raise AwaitingAsyncTask(base_msg)

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
            # Remove instances from the database
            for instance in instances_to_remove:
                instance.delete(self.resources.session)
                self.resources.session.commit()
