from typing import TYPE_CHECKING, Any, Optional, cast

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
from fides.service.manual_tasks.manual_task_instance_service import (
    ManualTaskInstanceService,
)
from fides.service.manual_tasks.utils import with_task_logging

if TYPE_CHECKING:
    from fides.api.models.manual_tasks.manual_task_instance import (
        ManualTaskInstance,
        ManualTaskSubmission,
    )


class ManualTaskService:
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ManualTaskConfigService(db)
        self.instance_service = ManualTaskInstanceService(db)

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

    @with_task_logging("Verify user IDs")
    def _non_existent_users(
        self, non_existent_user_ids: list[str], *, task_id: str
    ) -> None:
        """Get users by their IDs.

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

    # ------- User Management -------

    @with_task_logging("Assign users to task")
    def assign_users_to_task(
        self, task_id: str, user_ids: list[str]
    ) -> tuple[ManualTask, dict[str, Any]]:
        """Assigns users to this task. We can assign one or more users to a task. If any of the users do not exist,
        an error will be raised after the valid assignments are created.

        Args:
            task_id: The task ID (added for logging)
            user_ids: List of user IDs to assign

        Raises:
            ValueError: If any of the users do not exist

        Returns:
            tuple(ManualTask, log_details) The log_details are intercepted by the
            `with_task_logging` decorator. The task is returned to allow for chaining.
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

        details = {"assigned_users": sorted(list(users_to_assign))}
        log_data = {
            "task_id": task_id,
            "details": details,
        }

        # Track non-existent users
        non_existent_users = list(set(user_ids) - existing_users)
        try:
            self._non_existent_users(non_existent_users, task_id=task_id)
        except ValueError as e:
            # The decorator will create an error log when this exception is raised
            details["user_ids_not_assigned"] = sorted(non_existent_users)
            if len(users_to_assign) == 0:
                raise e

        return task, log_data

    @with_task_logging("Unassign users from task")
    def unassign_users_from_task(
        self, task_id: str, user_ids: list[str]
    ) -> tuple[ManualTask, dict[str, Any]]:
        """Remove the user assignment from this task.

        Args:
            task_id: The task ID (added for logging)
            user_ids: List of user IDs to unassign

        Returns:
            tuple(ManualTask, log_details) The log_details are intercepted by the
            `with_task_logging` decorator. The task is returned to allow for chaining.
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
            unassigned_user_ids = set(
                ref.reference_id for ref in references_to_unassign
            )

            # Delete references in bulk
            self.db.query(ManualTaskReference).filter(
                ManualTaskReference.id.in_(reference_ids)
            ).delete(synchronize_session=False)
            self.db.flush()
            self.db.refresh(task)

        # Check if any users weren't unassigned
        left_over_user_ids = [
            user_id for user_id in user_ids if user_id not in unassigned_user_ids
        ]

        # Return the task and log details for successful unassignments
        details = {
            "unassigned_users": (
                sorted(list(unassigned_user_ids)) if references_to_unassign else []
            )
        }
        log_data = {
            "task_id": task_id,
            "details": details,
        }

        if len(left_over_user_ids) > 0:
            try:
                self._non_existent_users(left_over_user_ids, task_id=task_id)
            except ValueError as e:
                # The decorator will create an error log when this exception is raised
                details["user_ids_not_unassigned"] = sorted(left_over_user_ids)
                if len(unassigned_user_ids) == 0:
                    raise e

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

    def create_instance(
        self, task_id: str, config_id: str, entity_id: str, entity_type: str
    ) -> "ManualTaskInstance":
        """Create a new instance for a task.

        Args:
            task_id: The task ID
            config_id: The config ID
            entity_id: The entity ID
            entity_type: The entity type

        Returns:
            ManualTaskInstance: The new instance
        """
        self.get_task(task_id=task_id)
        instance = self.instance_service.create_instance(
            task_id, config_id, entity_id, entity_type
        )
        return cast("ManualTaskInstance", instance)

    def create_submission(
        self, instance_id: str, field_id: str, data: dict[str, Any]
    ) -> "ManualTaskSubmission":
        """Create a new submission for a task.

        Args:
            instance_id: The instance ID
            field_id: The field ID
            data: The data for the submission

        Returns:
            ManualTaskSubmission: The new submission
        """
        submission = self.instance_service.create_submission(
            instance_id, field_id, data
        )
        return cast("ManualTaskSubmission", submission)
