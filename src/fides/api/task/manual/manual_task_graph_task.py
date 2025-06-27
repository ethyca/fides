from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import AwaitingAsyncTaskCallback
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskEntityType,
    ManualTaskInstance,
    StatusType,
    ManualTaskFieldType,
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
from fides.api.models.attachment import AttachmentType


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
        
        # Refresh manual tasks to ensure we have the latest config data
        for manual_task in manual_tasks:
            db.refresh(manual_task)

        # Check/create manual task instances
        self._ensure_manual_task_instances(db, manual_tasks, self.resources.request)

        # Check if all manual task instances have submissions
        submitted_data = self._get_submitted_data(
            db, manual_tasks, self.resources.request
        )

        if submitted_data is not None:
            # Convert submitted data to Row format for consistency with other collections
            result = [submitted_data] if submitted_data else []
            # Persist access data on the RequestTask so it can be included in the final package
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
    ) -> None:
        """Create ManualTaskInstances if they don't exist for this privacy request"""

        for manual_task in manual_tasks:
            # Check each active config for instances
            for config in manual_task.configs:
                if not config.is_current:
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
        Check if all manual task instances have submissions for ALL fields and return aggregated data
        Returns None if any field submissions are missing (all fields must be completed or skipped)
        """
        aggregated_data: Dict[str, Any] = {}
        def _format_size(size_bytes: int) -> str:
            units = ["B","KB","MB","GB","TB"]
            size = float(size_bytes)
            for unit in units:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} PB"

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

                # Check if instance has submissions for ALL fields (not just required)
                all_fields = config.field_definitions or []
                submissions = instance.submissions

                if not submissions:
                    return None

                # Check if we have submissions for ALL fields (completed or skipped)
                submitted_field_ids = {
                    submission.field_id for submission in submissions
                }
                all_field_ids = {field.id for field in all_fields}

                missing_field_ids = all_field_ids - submitted_field_ids
                if missing_field_ids:
                    return None

                # Update instance status to completed if not already
                if instance.status != StatusType.completed:
                    instance.status = StatusType.completed
                    instance.save(db)

                # Aggregate submission data
                for submission in submissions:
                    if not submission.field or not submission.field.field_key:
                        continue

                    field_key = submission.field.field_key
                    field_type = submission.data.get("field_type")

                    if field_type == ManualTaskFieldType.attachment.value:
                        # Build mapping of filenames to url/size for inline display
                        attachment_map: Dict[str, Dict[str, Any]] = {}
                        for attachment in (submission.attachments or []):
                            if (
                                attachment.attachment_type
                                == AttachmentType.include_with_access_package
                            ):
                                try:
                                    size, url = attachment.retrieve_attachment()
                                    attachment_map[attachment.file_name] = {
                                        "url": str(url) if url else None,
                                        "size": _format_size(size) if size else "Unknown",
                                    }
                                except Exception as e:  # pragma: no cover
                                    logger.warning(
                                        "Error retrieving attachment {}: {}",
                                        attachment.file_name,
                                        str(e),
                                    )

                        if attachment_map:
                            aggregated_data[field_key] = attachment_map
                        else:
                            aggregated_data[field_key] = None

                    else:
                        # Unwrap to the raw value for text/checkbox, etc.
                        aggregated_data[field_key] = submission.data.get("value")

        result = aggregated_data if aggregated_data else None
        return result

    def dry_run_task(self) -> int:
        """Return estimated row count for dry run - manual tasks don't have predictable counts"""
        return 1  # Placeholder - manual tasks generate variable data
