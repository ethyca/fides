from typing import Any, Optional, cast

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_tasks.manual_task import ManualTask, ManualTaskReference
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskParentEntityType,
    ManualTaskReferenceType,
    ManualTaskType,
)
from fides.service.manual_tasks.manual_task_config_service import (
    ManualTaskConfigService,
)
from fides.service.manual_tasks.utils import with_task_logging


class ManualTaskService:
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ManualTaskConfigService(db)

    def get_task(
        self,
        task_id: Optional[str] = None,
        parent_entity_id: Optional[str] = None,
        parent_entity_type: Optional[ManualTaskParentEntityType] = None,
        task_type: Optional[ManualTaskType] = None,
    ) -> ManualTask:
        """Get the manual task using provided filters.

        This is a flexible lookup method that can find tasks based on various filters.
        It's normal for this method to return None if no task matches the given filters.

        Args:
            task_id: The task ID
            parent_entity_id: The parent entity ID
            parent_entity_type: The parent entity type
            task_type: The task type

        Returns:
            ManualTask: The matching task
        """
        if not any([task_id, parent_entity_id, parent_entity_type, task_type]):
            logger.debug("No filters provided to get_task")
            raise ValueError("No filters provided to get_task")

        # Build filter conditions and a human-readable description
        filters = []
        filter_desc = []
        if task_id:
            filters.append(ManualTask.id == task_id)
            filter_desc.append(f"task_id={task_id}")
        if parent_entity_id:
            filters.append(ManualTask.parent_entity_id == parent_entity_id)
            filter_desc.append(f"parent_entity_id={parent_entity_id}")
        if parent_entity_type:
            filters.append(ManualTask.parent_entity_type == parent_entity_type)
            filter_desc.append(f"parent_entity_type={parent_entity_type}")
        if task_type:
            filters.append(ManualTask.task_type == task_type)
            filter_desc.append(f"task_type={task_type}")

        # Apply all filters at once
        stmt = select(ManualTask)  # type: ignore[arg-type]
        if filters:
            stmt = stmt.where(*filters)

        task = self.db.execute(stmt).scalar_one_or_none()
        if task is None:
            logger.debug(f"No task found with filters: {filter_desc}")
            raise ValueError(f"No task found with filters: {filter_desc}")
        return task

    @with_task_logging("Provided user IDs verified")
    def _non_existent_users(
        self, non_existent_user_ids: list[str], *, task_id: str
    ) -> None:
        """This is a helper function to raise an error if users do not exist.
        If non_existent_user_ids is empty, this function will instead create
        a success log entry.

        Args:
            non_existent_user_ids: List of non-existent user IDs
            task_id: The task ID

        Returns:
            None
        """
        if len(non_existent_user_ids) > 0:
            raise ValueError(
                f"User(s) {sorted(list(non_existent_user_ids))} do not exist"
            )

    def _create_log_data(self, task_id: str, details: dict[str, Any]) -> dict[str, Any]:
        """Create standard log data structure.

        Args:
            task_id: The task ID
            details: The log details

        Returns:
            dict: The log data structure
        """
        return {
            "task_id": task_id,
            "details": details,
        }

    def _handle_user_errors(
        self,
        non_existent_users: list[str],
        task_id: str,
        details: dict[str, Any],
        success_count: int,
        error_key: str,
    ) -> None:
        """Handle errors for non-existent users.

        Args:
            non_existent_users: List of non-existent user IDs
            task_id: The task ID
            details: The log details to update
            success_count: Number of successful operations
            error_key: Key to use for error details

        Raises:
            ValueError: If no successful operations and users don't exist
        """
        try:
            self._non_existent_users(non_existent_users, task_id=task_id)
        except ValueError as e:
            details[error_key] = sorted(non_existent_users)
            if success_count == 0:
                raise e

    def _get_existing_users(self, user_ids: list[str]) -> set[str]:
        """Get set of existing user IDs from the provided list.

        Args:
            user_ids: List of user IDs to check

        Returns:
            set: Set of existing user IDs
        """
        return set(
            user.id
            for user in self.db.query(FidesUser)
            .filter(FidesUser.id.in_(user_ids))
            .all()
        )

    def _handle_user_operation(
        self,
        task_id: str,
        user_ids: list[str],
        operation_type: str,
        current_users: Optional[set[str]] = None,
    ) -> tuple[set[str], dict[str, Any]]:
        """Handle user assignment/unassignment operations.

        Args:
            task_id: The task ID
            user_ids: List of user IDs to process
            operation_type: Type of operation ('assign' or 'unassign')
            current_users: Optional set of current users

        Returns:
            tuple: (processed_users, log_data)
        """
        if not (user_ids := list(set(user_ids))):
            raise ValueError(f"User ID is required for {operation_type}ment")

        existing_users = set(
            u.id
            for u in self.db.query(FidesUser).filter(FidesUser.id.in_(user_ids)).all()
        )
        processed_users = (
            existing_users - (current_users or set())
            if operation_type == "assign"
            else existing_users
        )
        details = {f"{operation_type}ed_users": sorted(list(processed_users))}

        if non_existing := list(set(user_ids) - existing_users):
            try:
                self._non_existent_users(non_existing, task_id=task_id)
            except ValueError as e:
                details[f"user_ids_not_{operation_type}ed"] = sorted(non_existing)
                if not processed_users:
                    raise e

        return processed_users, {"task_id": task_id, "details": details}

    @with_task_logging("Assign users to task")
    def assign_users_to_task(
        self, task_id: str, user_ids: list[str]
    ) -> tuple[ManualTask, dict[str, Any]]:
        """Assign users to a task.

        Args:
            task_id: The task ID
            user_ids: List of user IDs to assign

        Returns:
            Tuple containing the task and log data, the log data is
            captured by the with_task_logging decorator. and the task is
            returned to the caller.
        """
        task = self.get_task(task_id=task_id)
        users_to_assign, log_data = self._handle_user_operation(
            task_id, user_ids, "assign", set(task.assigned_users)
        )

        if users_to_assign:
            self.db.bulk_insert_mappings(
                ManualTaskReference,
                [
                    {
                        "task_id": task.id,
                        "reference_id": user_id,
                        "reference_type": ManualTaskReferenceType.assigned_user,
                    }
                    for user_id in users_to_assign
                ],
            )
            self.db.flush()
            self.db.refresh(task)

        return task, log_data

    @with_task_logging("Unassign users from task")
    def unassign_users_from_task(
        self, task_id: str, user_ids: list[str]
    ) -> tuple[ManualTask, dict[str, Any]]:
        task = self.get_task(task_id=task_id)
        refs_to_unassign = (
            self.db.query(ManualTaskReference)
            .filter(
                ManualTaskReference.task_id == task.id,
                ManualTaskReference.reference_type
                == ManualTaskReferenceType.assigned_user,
                ManualTaskReference.reference_id.in_(user_ids),
            )
            .all()
        )

        if refs_to_unassign:
            self.db.query(ManualTaskReference).filter(
                ManualTaskReference.id.in_([ref.id for ref in refs_to_unassign])
            ).delete(synchronize_session=False)
            self.db.flush()
            self.db.refresh(task)

        _, log_data = self._handle_user_operation(task_id, user_ids, "unassign")
        return task, log_data

    def create_config(
        self, config_type: str, fields: list[dict], task_id: str
    ) -> ManualTaskConfig:
        """Create a new config for a task.

        Args:
            config_type: The config type
            fields: The fields for the config
            task_id: The task ID

        Returns:
            ManualTaskConfig: The new config
        """
        task = self.get_task(task_id=task_id)
        config = self.config_service.create_new_version(task, config_type, fields)
        return cast(ManualTaskConfig, config)

    def delete_config(self, config: ManualTaskConfig, task_id: str) -> None:
        """Delete this configuration.
        Args:
            config: The config to delete
            task_id: The task ID
        Raises:
            ValueError: If there are active instances using this configuration
            ValueError: If the task does not exist

        Returns:
            dict[str, Any]: The log details - intercepted by the `with_task_logging` decorator.
        """
        task = self.get_task(task_id=task_id)

        # Delete the configuration
        config_id = config.id
        self.config_service.delete_config(task, config_id)
