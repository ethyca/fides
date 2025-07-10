from typing import Any, Dict, List, Optional

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
    StatusType,
)
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.graph_task import GraphTask, retry
from fides.api.task.manual.manual_task_utils import (
    ManualTaskAddress,
    get_manual_tasks_for_connection_config,
)
from fides.api.util.collection_util import Row


class ManualTaskGraphTask(GraphTask):
    """GraphTask implementation for ManualTask execution"""

    @retry(action_type=ActionType.access, default_return=[])
    def access_request(self, *inputs: List[Row]) -> List[Row]:
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
        manual_tasks = get_manual_tasks_for_connection_config(db, connection_key)

        if not manual_tasks:
            return []

        # Check/create manual task instances for ACCESS configs only
        self._ensure_manual_task_instances(
            db,
            manual_tasks,
            self.resources.request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        # Check if all manual task instances have submissions for ACCESS configs only
        submitted_data = self._get_submitted_data(
            db,
            manual_tasks,
            self.resources.request,
            ManualTaskConfigurationType.access_privacy_request,
        )

        if submitted_data is not None:
            result: List[Row] = [submitted_data] if submitted_data else []
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
        manual_tasks: List[ManualTask],
        privacy_request: PrivacyRequest,
        allowed_config_type: "ManualTaskConfigurationType",
    ) -> None:
        """Create ManualTaskInstances for configs matching `allowed_config_type` if they don't exist."""

        for manual_task in manual_tasks:
            # ------------------------------------------------------------------
            # Short-circuit: if instances already exist for this task & entity
            # (no matter what config version they were created for) we should reuse
            # them instead of creating a brand-new one that would result in
            # duplicates when configurations are versioned after the privacy
            # request has started.
            # ------------------------------------------------------------------
            existing_task_instance = (
                db.query(ManualTaskInstance)
                .filter(
                    ManualTaskInstance.task_id == manual_task.id,
                    ManualTaskInstance.entity_id == privacy_request.id,
                    ManualTaskInstance.entity_type
                    == ManualTaskEntityType.privacy_request,
                )
                .first()
            )
            if existing_task_instance:
                # An instance already exists for this privacy request – no need
                # to create another one tied to a newer config version.
                continue

            # Check each active config for instances (now we know none exist yet)
            for config in manual_task.configs:
                if not config.is_current or config.config_type != allowed_config_type:
                    # Skip configs that are not current or not relevant for this request type
                    continue

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

    # pylint: disable=too-many-branches,too-many-nested-blocks
    def _get_submitted_data(
        self,
        db: Session,
        manual_tasks: List[ManualTask],
        privacy_request: PrivacyRequest,
        allowed_config_type: "ManualTaskConfigurationType",
    ) -> Optional[Dict[str, Any]]:
        """
        Check if all manual task instances have submissions for ALL fields and return aggregated data
        Returns None if any field submissions are missing (all fields must be completed or skipped)
        """
        aggregated_data: Dict[str, Any] = {}

        def _format_size(size_bytes: int) -> str:
            units = ["B", "KB", "MB", "GB", "TB"]
            size = float(size_bytes)
            for unit in units:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} PB"

        for manual_task in manual_tasks:

            candidate_instances: list[ManualTaskInstance] = (
                db.query(ManualTaskInstance)
                .filter(
                    ManualTaskInstance.task_id == manual_task.id,
                    ManualTaskInstance.entity_id == privacy_request.id,
                    ManualTaskInstance.entity_type
                    == ManualTaskEntityType.privacy_request,
                )
                .all()
            )

            if not candidate_instances:
                return None  # No instance yet for this manual task

            for inst in candidate_instances:
                # Skip instances tied to other request types
                if not inst.config or inst.config.config_type != allowed_config_type:
                    continue

                all_fields = inst.config.field_definitions or []

                # Every field must have a submission
                if not all(inst.get_submission_for_field(f.id) for f in all_fields):
                    return None  # At least one instance still incomplete

                # Ensure status set
                if inst.status != StatusType.completed:
                    inst.status = StatusType.completed
                    inst.save(db)

                # Aggregate submission data from this instance
                for submission in inst.submissions:
                    if not submission.field or not submission.field.field_key:
                        continue

                    field_key = submission.field.field_key

                    if not isinstance(submission.data, dict):
                        continue

                    data_dict: Dict[str, Any] = submission.data

                    field_type = data_dict.get("field_type")

                    if field_type == ManualTaskFieldType.attachment.value:
                        attachment_map: Dict[str, Dict[str, Any]] = {}
                        for attachment in submission.attachments or []:
                            if (
                                attachment.attachment_type
                                == AttachmentType.include_with_access_package
                            ):
                                try:
                                    size, url = attachment.retrieve_attachment()
                                    attachment_map[attachment.file_name] = {
                                        "url": str(url) if url else None,
                                        "size": (
                                            _format_size(size) if size else "Unknown"
                                        ),
                                    }
                                except (
                                    Exception
                                ) as exc:  # pylint: disable=broad-exception-caught
                                    logger.warning(
                                        "Error retrieving attachment {}: {}",
                                        attachment.file_name,
                                        str(exc),
                                    )

                        aggregated_data[field_key] = attachment_map or None
                    else:
                        aggregated_data[field_key] = data_dict.get("value")

        return aggregated_data if aggregated_data else None

    def dry_run_task(self) -> int:
        """Return estimated row count for dry run - manual tasks don't have predictable counts"""
        return 1  # Placeholder - manual tasks generate variable data

    # NEW METHOD: Provide erasure support for manual tasks
    @retry(action_type=ActionType.erasure, default_return=0)
    def erasure_request(
        self,
        retrieved_data: List[Row],
        *erasure_prereqs: int,  # noqa: D401, pylint: disable=unused-argument
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
        manual_tasks = get_manual_tasks_for_connection_config(db, connection_key)
        if not manual_tasks:
            # No manual tasks defined – nothing to erase
            self.log_end(ActionType.erasure)
            return 0

        # Create ManualTaskInstances for ERASURE configs only
        self._ensure_manual_task_instances(
            db,
            manual_tasks,
            self.resources.request,
            ManualTaskConfigurationType.erasure_privacy_request,
        )

        # Check for full submissions – reuse helper used by access flow, filtering ERASURE configs
        submissions_complete = self._get_submitted_data(
            db,
            manual_tasks,
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
