from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.manual_tasks.manual_task import ManualTask, ManualTaskReference
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskLogStatus,
    ManualTaskParentEntityType,
    ManualTaskReferenceType,
    ManualTaskType,
)


class ManualTaskService:
    def __init__(self, db: Session):
        self.db = db

    def get_task(
        self,
        task_id: Optional[str] = None,
        parent_entity_id: Optional[str] = None,
        parent_entity_type: Optional[ManualTaskParentEntityType] = None,
        task_type: Optional[ManualTaskType] = None,
    ) -> Optional[ManualTask]:
        """Get the manual task using provided filters.

        Args:
            task_id: The task ID
            parent_entity_id: The parent entity ID
            parent_entity_type: The parent entity type
            task_type: The task type

        Returns:
            Optional[ManualTask]: The manual task for the connection, if it exists
        """
        if not any([task_id, parent_entity_id, parent_entity_type, task_type]):
            logger.warning("No filters provided to get_task. Returning None.")
            return None

        stmt = select(ManualTask)  # type: ignore[arg-type]
        if task_id:
            stmt = stmt.where(ManualTask.id == task_id)
        if parent_entity_id:
            stmt = stmt.where(ManualTask.parent_entity_id == parent_entity_id)
        if parent_entity_type:
            stmt = stmt.where(ManualTask.parent_entity_type == parent_entity_type)
        if task_type:
            stmt = stmt.where(ManualTask.task_type == task_type)
        return self.db.execute(stmt).scalar_one_or_none()

    # User Management
    def assign_users_to_task(
        self, db: Session, task: ManualTask, user_ids: list[str]
    ) -> None:
        """Assigns users to this task. We can assign one or more users to a task.

        Args:
            db: Database session
            task: The task to assign users to
            user_ids: List of user IDs to assign
        """
        user_ids = list(set(user_ids))
        if not user_ids:
            raise ValueError("User ID is required for assignment")

        # Create new user assignment
        for user_id in user_ids:
            # if user is already assigned, skip
            if user_id in task.assigned_users:
                continue
            # verify user exists
            user = db.query(FidesUser).filter_by(id=user_id).first()
            if not user:
                ManualTaskLog.create_error_log(
                    db=db,
                    task_id=task.id,
                    message=f"Failed to add user {user_id} to task {task.id}: user does not exist",
                    details={"user_id": user_id},
                )
                continue

            ManualTaskReference.create(
                db=db,
                data={
                    "task_id": task.id,
                    "reference_id": user_id,
                    "reference_type": ManualTaskReferenceType.assigned_user,
                },
            )

            # Log the user assignment
            ManualTaskLog.create_log(
                db=db,
                task_id=task.id,
                status=ManualTaskLogStatus.updated,
                message=f"User {user_id} assigned to task",
                details={"assigned_user_id": user_id},
            )

    def unassign_users_from_task(
        self, db: Session, task: ManualTask, user_ids: list[str]
    ) -> None:
        """Remove the user assignment from this task.

        Args:
            db: Database session
            task: The task to unassign users from
            user_ids: List of user IDs to unassign
        """
        user_ids = list(set(user_ids))
        if not user_ids:
            raise ValueError("User ID is required for unassignment")

        # Get references to unassign
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

        # Delete references and log unassignments
        for ref in references_to_unassign:
            ref.delete(db)
            ManualTaskLog.create_log(
                db=db,
                task_id=task.id,
                status=ManualTaskLogStatus.updated,
                message=f"User {ref.reference_id} unassigned from task",
                details={"unassigned_user_id": ref.reference_id},
            )

        # Check if any users weren't unassigned
        unassigned_user_ids = [ref.reference_id for ref in references_to_unassign]
        left_over_user_ids = [
            user_id for user_id in user_ids if user_id not in unassigned_user_ids
        ]
        if left_over_user_ids:
            logger.warning(
                f"Failed to unassign users {left_over_user_ids} from task {task.id}: "
                "users were not assigned to the task"
            )
