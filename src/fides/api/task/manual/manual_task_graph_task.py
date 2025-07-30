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

        # Get manual tasks for this connection
        manual_task = get_manual_task_for_connection_config(db, connection_key)

        if not manual_task:
            return []

        # Check if any manual tasks have ACCESS configs
        # TODO: This will be changed with Manual Task Dependencies Implementation.

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

        # Fetch relevant manual tasks for this connection
        manual_task = get_manual_task_for_connection_config(db, connection_key)
        if not manual_task:
            # No manual tasks defined – nothing to erase
            self.log_end(ActionType.erasure)
            return 0

        # Check if any manual tasks have ERASURE configs
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
