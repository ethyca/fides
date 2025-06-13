from typing import Any, Optional

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
from fides.service.manual_tasks.utils import with_error_logging


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
    ) -> Optional[ManualTask]:
        """Get the manual task using provided filters.

        This is a flexible lookup method that can find tasks based on various filters.
        It's normal for this method to return None if no task matches the given filters.

        Args:
            task_id: The task ID
            parent_entity_id: The parent entity ID
            parent_entity_type: The parent entity type
            task_type: The task type

        Returns:
            Optional[ManualTask]: The matching task if found, None otherwise
        """
        if not any([task_id, parent_entity_id, parent_entity_type, task_type]):
            logger.debug("No filters provided to get_task. Returning None.")
            return None

        # Build filter conditions
        filters = []
        if task_id:
            filters.append(ManualTask.id == task_id)
        if parent_entity_id:
            filters.append(ManualTask.parent_entity_id == parent_entity_id)
        if parent_entity_type:
            filters.append(ManualTask.parent_entity_type == parent_entity_type)
        if task_type:
            filters.append(ManualTask.task_type == task_type)

        # Apply all filters at once
        stmt = select(ManualTask)  # type: ignore[arg-type]
        if filters:
            stmt = stmt.where(*filters)

        return self.db.execute(stmt).scalar_one_or_none()

    # ------- User Management -------

    @with_error_logging("Verify user IDs")
    def _non_existent_users(
        self, task_id: str, non_existent_user_ids: list[str]
    ) -> None:
        """Get users by their IDs.

        Args:
            task_id: The task ID
            non_existent_user_ids: List of non-existent user IDs
        """
        if len(non_existent_user_ids) > 0:
            raise ValueError(
                f"User(s) {sorted(list(non_existent_user_ids))} do not exist"
            )

    @with_error_logging("Assign users to task")
    def assign_users_to_task(self, task_id: str, user_ids: list[str]) -> dict[str, Any]:
        """Assigns users to this task. We can assign one or more users to a task. If any of the users do not exist,
        an error will be raised after the valid assignments are created.

        Args:
            task_id: The task ID (added for logging)
            user_ids: List of user IDs to assign

        Raises:
            ValueError: If any of the users do not exist
        """
        task = self.get_task(task_id=task_id)
        user_ids = list(set(user_ids))  # Remove duplicates
        if not user_ids:
            raise ValueError("User ID is required for assignment")

        # Get current assigned users
        current_assigned_users = set(task.assigned_users)

        # Get all existing users to assign
        existing_users = set(
            user.id
            for user in self.db.query(FidesUser)
            .filter(FidesUser.id.in_(user_ids))
            .all()
        )

        # Track non-existent user
        try:
            self._non_existent_users(
                task_id=task_id, non_existent_user_ids=set(user_ids) - existing_users
            )
        except ValueError as e:
            logger.error(f"Error in Assign users to task: {e}")

        # Process valid assignments first
        users_to_assign = existing_users - current_assigned_users

        # Prepare bulk insert data for valid assignments
        assignments_to_create = [
            {
                "task_id": task.id,
                "reference_id": user_id,
                "reference_type": ManualTaskReferenceType.assigned_user,
            }
            for user_id in users_to_assign
        ]

        # Create assignments in bulk
        if assignments_to_create:
            self.db.bulk_insert_mappings(ManualTaskReference, assignments_to_create)
            self.db.flush()
            self.db.refresh(task)

        return {
            "task_id": task_id,
            "details": {"assigned_users": sorted(list(users_to_assign))},
        }

    @with_error_logging("Unassign users from task")
    def unassign_users_from_task(
        self, task_id: str, user_ids: list[str]
    ) -> dict[str, Any]:
        """Remove the user assignment from this task.

        Args:
            task_id: The task ID (added for logging)
            user_ids: List of user IDs to unassign
        """
        task = self.get_task(task_id=task_id)
        user_ids = list(set(user_ids))  # Remove duplicates
        if not user_ids:
            raise ValueError("User ID is required for unassignment")

        # Get references to unassign in a single query
        references_to_unassign = (
            self.db.query(ManualTaskReference)
            .filter(
                ManualTaskReference.task_id == task.id,
                ManualTaskReference.reference_type
                == ManualTaskReferenceType.assigned_user,
                ManualTaskReference.reference_id.in_(user_ids),
            )
            .all()
        )

        unassigned_user_ids: set[str] = set()
        if references_to_unassign:
            # Capture reference IDs before deletion
            reference_ids = [ref.id for ref in references_to_unassign]
            unassigned_user_ids = [ref.reference_id for ref in references_to_unassign]

            # Delete references in bulk
            self.db.query(ManualTaskReference).filter(
                ManualTaskReference.id.in_(reference_ids)
            ).delete(synchronize_session=False)
            self.db.flush()
            self.db.refresh(task)

        # Check if any users weren't unassigned
        unassigned_user_ids_set = (
            set(unassigned_user_ids) if references_to_unassign else set()
        )
        left_over_user_ids = [
            user_id for user_id in user_ids if user_id not in unassigned_user_ids_set
        ]
        if left_over_user_ids:
            logger.debug(
                f"Users {left_over_user_ids} were not unassigned from task {task.id}: "
                "users were not assigned to the task"
            )

        return {
            "task_id": task_id,
            "details": {
                "unassigned_users": (
                    sorted(unassigned_user_ids) if references_to_unassign else []
                )
            },
        }

    def create_config(
        self, config_type: str, fields: list[dict], task_id: str
    ) -> ManualTaskConfig:
        """Create a new config for a task.

        Args:
            config_type: The config type
            fields: The fields for the config
            task_id: The task ID
        """
        task = self.get_task(task_id=task_id)
        config = self.config_service.create_new_version(task, config_type, fields)
        return config

    def delete_config(self, config: ManualTaskConfig, task_id: str) -> None:
        """Delete this configuration.
        Args:
            config: The config to delete
            task_id: The task ID
        Raises:
            ValueError: If there are active instances using this configuration
            ValueError: If the task does not exist
        """
        task = self.get_task(task_id=task_id)
        if task is None:
            raise ValueError(f"Task with ID {task_id} not found")

        # Delete the configuration
        self.config_service.delete_config(task, config.id)
