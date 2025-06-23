from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import AwaitingAsyncTaskCallback
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskEntityType,
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

        # Check/create manual task instances
        self._ensure_manual_task_instances(db, manual_tasks, self.resources.request)

        # Check if all manual task instances have submissions
        submitted_data = self._get_submitted_data(
            db, manual_tasks, self.resources.request
        )

        if submitted_data is not None:
            # Convert submitted data to Row format for consistency with other collections
            return [submitted_data] if submitted_data else []

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
    ) -> None:
        """Create ManualTaskInstances if they don't exist for this privacy request"""

        for manual_task in manual_tasks:
            # Check each active config for instances
            for config in manual_task.configs:
                if not config.is_current:
                    logger.info(f"[DEBUG] Skipping config {config.id} - not current")
                    continue

                existing_instance = (
                    db.query(ManualTaskInstance)
                    .filter(
                        ManualTaskInstance.task_id == manual_task.id,
                        ManualTaskInstance.config_id == config.id,
                        ManualTaskInstance.entity_id == privacy_request.id,
                        ManualTaskInstance.entity_type
                        == ManualTaskEntityType.privacy_request,
                    )
                    .first()
                )

                if not existing_instance:
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
        manual_tasks: List[ManualTask],
        privacy_request: PrivacyRequest,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if all manual task instances have submissions and return aggregated data
        Returns None if any submissions are missing
        """
        aggregated_data: Dict[str, Dict[str, Any]] = {}

        for manual_task in manual_tasks:
            for config in manual_task.configs:
                if not config.is_current:
                    continue

                instance = (
                    db.query(ManualTaskInstance)
                    .filter(
                        ManualTaskInstance.task_id == manual_task.id,
                        ManualTaskInstance.config_id == config.id,
                        ManualTaskInstance.entity_id == privacy_request.id,
                        ManualTaskInstance.entity_type
                        == ManualTaskEntityType.privacy_request,
                    )
                    .first()
                )

                if not instance:
                    return None

                # Check if instance has submissions for all required fields
                required_fields = [
                    field
                    for field in config.field_definitions
                    if field.field_metadata.get("required", False)
                ]
                submissions = instance.submissions

                if not submissions:
                    return None

                # Check if we have submissions for all required fields
                submitted_field_ids = {
                    submission.field_id for submission in submissions
                }
                required_field_ids = {field.id for field in required_fields}

                if not required_field_ids.issubset(submitted_field_ids):
                    return None

                # Aggregate submission data
                task_data = {}
                for submission in submissions:
                    if submission.field and submission.field.field_key:
                        task_data[submission.field.field_key] = submission.data

                # Group by task ID
                task_key = f"task_{manual_task.id}"
                if task_key not in aggregated_data:
                    aggregated_data[task_key] = {}
                aggregated_data[task_key].update(task_data)

        result = aggregated_data if aggregated_data else None
        return result

    def dry_run_task(self) -> int:
        """Return estimated row count for dry run - manual tasks don't have predictable counts"""
        return 1  # Placeholder - manual tasks generate variable data
