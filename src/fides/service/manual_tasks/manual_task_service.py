from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_tasks.manual_task import ManualTask, ManualTaskReference
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskLogStatus,
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

    @with_error_logging("Get task")
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

    # User Management
    @with_error_logging("Assign users to task")
    def assign_users_to_task(
        self, db: Session, task: ManualTask, user_ids: list[str]
    ) -> None:
        """Assigns users to this task. We can assign one or more users to a task.

        Args:
            db: Database session
            task: The task to assign users to
            user_ids: List of user IDs to assign
        """
        user_ids = list(set(user_ids))  # Remove duplicates
        if not user_ids:
            raise ValueError("User ID is required for assignment")

        # Get current assigned users
        current_assigned_users = set(task.assigned_users)

        # Get all existing users to assign
        existing_users = set(
            user.id
            for user in db.query(FidesUser).filter(FidesUser.id.in_(user_ids)).all()
        )
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
            db.bulk_insert_mappings(ManualTaskReference, assignments_to_create)
            db.flush()
            db.refresh(task)

        # Log errors for non-existent users
        for user_id in user_ids:
            if user_id not in existing_users:
                raise ValueError(f"User {user_id} does not exist")

    @with_error_logging("Unassign users from task")
    def unassign_users_from_task(
        self, db: Session, task: ManualTask, user_ids: list[str]
    ) -> None:
        """Remove the user assignment from this task.

        Args:
            db: Database session
            task: The task to unassign users from
            user_ids: List of user IDs to unassign
        """
        user_ids = list(set(user_ids))  # Remove duplicates
        if not user_ids:
            raise ValueError("User ID is required for unassignment")

        # Get references to unassign in a single query
        references_to_unassign = (
            db.query(ManualTaskReference)
            .filter(
                ManualTaskReference.task_id == task.id,
                ManualTaskReference.reference_type
                == ManualTaskReferenceType.assigned_user,
                ManualTaskReference.reference_id.in_(user_ids),
            )
            .all()
        )

        if references_to_unassign:
            # Capture reference IDs before deletion
            reference_ids = [ref.id for ref in references_to_unassign]

            # Delete references in bulk
            db.query(ManualTaskReference).filter(
                ManualTaskReference.id.in_(reference_ids)
            ).delete(synchronize_session=False)
            db.flush()
            db.refresh(task)

        # Check if any users weren't unassigned
        unassigned_user_ids = [ref.reference_id for ref in references_to_unassign]
        unassigned_user_ids_set = set(unassigned_user_ids)
        left_over_user_ids = [
            user_id for user_id in user_ids if user_id not in unassigned_user_ids_set
        ]
        if left_over_user_ids:
            logger.debug(
                f"Users {left_over_user_ids} were not unassigned from task {task.id}: "
                "users were not assigned to the task"
            )

    @with_error_logging("Create task configuration")
    def create_config(
        self, task: ManualTask, config_type: str, fields: list[dict]
    ) -> None:
        """Create a new config for a task.

        Args:
            task: The task to create config for
            config_type: The config type
            fields: The fields for the config
        """
        self.config_service.create_new_version(task, config_type, fields)

    @with_error_logging("Delete task configuration")
    def delete_config(self, task: ManualTask, config: ManualTaskConfig) -> None:
        """Delete this configuration.
        Args:
            db: Database session
            task: The task to delete the config from
            config: The config to delete
        Raises:
            ValueError: If there are active instances using this configuration
        """
        # TODO: when instances are implemented, we need to check for active instances

        # Log the deletion
        ManualTaskLog.create_log(
            db=self.db,
            task_id=task.id,
            config_id=None,
            status=ManualTaskLogStatus.complete,
            message=f"Deleted manual task configuration for {config.config_type}",
        )

        # Delete the configuration
        self.config_service.delete_config(task, config.id)
