from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

from loguru import logger
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
from fides.api.models.manual_tasks.manual_task_instance import (
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_config import ManualTaskFieldBase
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus
from fides.api.schemas.manual_tasks.manual_task_status import (
    StatusTransitionNotAllowed,
    StatusType,
)

T = TypeVar("T")
V = TypeVar("V")  # For validator return type


def validate_fields(fields: list[dict[str, Any]], is_submission: bool = False) -> None:
    """Validate field data against the appropriate Pydantic model.
    Raises a ValueError if the field data is invalid.

    Args:
        fields: List of field data to validate
        is_submission: Whether the fields are for a submission (True) or configuration (False)
    """
    # Check for duplicate field keys
    field_keys_set: set[str] = {str(field.get("field_key")) for field in fields}
    if len(field_keys_set) != len(fields):
        raise ValueError(
            "Duplicate field keys found in field updates, field keys must be unique."
        )
    # Check that field_key is present for each field
    for field in fields:
        field_key = field.get("field_key")
        if not field_key:
            raise ValueError("Invalid field data: field_key is required")
        # Skip validation for fields with empty metadata (used for removal)
        if not is_submission and field.get("field_metadata") == {}:
            continue

        try:
            field_type = field.get("field_type")
            if not field_type:
                raise ValueError("Invalid field data: field_type is required")

            if is_submission:
                # For submissions, we only need to validate the value
                if "value" not in field:
                    raise ValueError(
                        "Invalid field data: value is required for submissions"
                    )
            else:
                # For configurations, we need to validate the field metadata
                field_model = ManualTaskFieldBase.get_field_model_for_type(field_type)
                field_model.model_validate(field)
        except ValidationError as e:
            raise ValueError(f"Invalid field data: {str(e)}")
        except ValueError as e:
            raise ValueError(str(e))


def validate_status_transition(
    current_status: StatusType, new_status: StatusType
) -> None:
    """Validate that a status transition is allowed.

    Args:
        current_status: The current status
        new_status: The new status to transition to

    Raises:
        StatusTransitionNotAllowed: If the transition is not allowed
    """
    # Don't allow transitions to the same status
    if new_status == current_status:
        raise StatusTransitionNotAllowed(
            f"Invalid status transition: already in status {new_status}"
        )

    # Get valid transitions for current status
    valid_transitions = StatusType.get_valid_transitions(current_status)
    if new_status not in valid_transitions:
        raise StatusTransitionNotAllowed(
            f"Invalid status transition from {current_status} to {new_status}. "
            f"Valid transitions are: {valid_transitions}"
        )


def create_operation_logs(
    task_id: str,
    config_id: Optional[str],
    instance_id: Optional[str],
    operation: str,
    details: Optional[dict] = None,
    error: Optional[Exception] = None,
) -> list[dict]:
    """Create standard log entries for operations.

    Args:
        task_id: The task ID
        config_id: The config ID
        instance_id: The instance ID
        operation: Description of the operation
        details: Additional details for success log
        error: Exception for error log

    Returns:
        list[dict]: Log entries to create
    """
    if error:
        return [
            create_error_log(
                task_id=task_id,
                config_id=config_id,
                instance_id=instance_id,
                error=error,
                context=details or {},
            )
        ]

    return [
        {
            "task_id": task_id,
            "config_id": config_id,
            "instance_id": instance_id,
            "status": ManualTaskLogStatus.complete,
            "message": operation,
            "details": details or {},
        }
    ]


def with_error_logging(
    operation_name: str,
    success_status: ManualTaskLogStatus = ManualTaskLogStatus.complete,
):
    """Decorator for logging operation success/failure in service methods.

    This decorator handles:
    1. Success/failure logging for service operations
    2. Automatic creation of ManualTaskLog entries
    3. Proper error propagation

    Args:
        operation_name: Name of the operation being performed
        success_status: Status to use for successful operations (defaults to complete)

    Returns:
        Decorator function that wraps service methods with error logging
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                result = func(self, *args, **kwargs)

                # Create success log if we have task_id
                task_id = None
                config_id = None
                instance_id = None
                details = {}

                # Try to get IDs and details from result object
                if isinstance(result, dict):
                    # Handle dictionary results
                    task_id = result.get("task_id")
                    config_id = result.get("config_id")
                    instance_id = result.get("instance_id")
                    details = result.get("details", {})
                elif hasattr(result, "task_id"):
                    # Handle model objects
                    task_id = result.task_id
                    if hasattr(result, "id"):
                        if isinstance(result, ManualTaskConfig):
                            config_id = result.id
                        elif isinstance(result, ManualTaskInstance):
                            instance_id = result.id

                # Try to get IDs from kwargs if not in result
                if not task_id and "task_id" in kwargs:
                    task_id = kwargs["task_id"]
                    config_id = kwargs.get("config_id")
                    instance_id = kwargs.get("instance_id")

                # Debug logging
                logger.debug(f"Creating log for operation {operation_name}")
                logger.debug(f"task_id: {task_id}")
                logger.debug(f"config_id: {config_id}")
                logger.debug(f"instance_id: {instance_id}")
                logger.debug(f"details: {details}")
                logger.debug(f"kwargs: {kwargs}")
                logger.debug(f"result type: {type(result)}")
                if hasattr(result, "__dict__"):
                    logger.debug(f"result attrs: {result.__dict__}")

                # Only create log if we have a task_id
                if task_id and hasattr(self, "db"):
                    ManualTaskLog.create_log(
                        db=self.db,
                        task_id=task_id,
                        config_id=config_id,
                        instance_id=instance_id,
                        status=success_status,
                        message=operation_name,
                        details=details,
                    )

                return result

            except Exception as e:
                # Log the error
                logger.error(f"Error in {operation_name}: {str(e)}")
                logger.debug(f"Error kwargs: {kwargs}")

                # Create error log if we have task_id and db
                task_id = kwargs.get("task_id")
                if task_id and hasattr(self, "db"):
                    ManualTaskLog.create_log(
                        db=self.db,
                        task_id=task_id,
                        config_id=kwargs.get("config_id"),
                        instance_id=kwargs.get("instance_id"),
                        status=ManualTaskLogStatus.error,
                        message=f"Error in {operation_name}: {str(e)}",
                        details=kwargs.get("details", {}),
                    )
                raise

        return wrapper

    return decorator


def create_status_change_log(
    task_id: str,
    config_id: Optional[str],
    instance_id: Optional[str],
    previous_status: StatusType,
    new_status: StatusType,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    """Create a log entry for a status change.

    Args:
        task_id: The task ID
        config_id: The config ID
        instance_id: The instance ID
        previous_status: The previous status
        new_status: The new status
        user_id: The user ID making the change

    Returns:
        The log entry data
    """
    return {
        "task_id": task_id,
        "config_id": config_id,
        "instance_id": instance_id,
        "status": ManualTaskLogStatus.in_progress,
        "message": f"Task instance status transitioning from {previous_status} to {new_status}",
        "details": {
            "previous_status": previous_status,
            "new_status": new_status,
            "user_id": user_id,
        },
    }


def create_error_log(
    task_id: str,
    config_id: Optional[str],
    instance_id: Optional[str],
    error: Exception,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Create a log entry for an error.

    Args:
        task_id: The task ID
        config_id: The config ID
        instance_id: The instance ID
        error: The error that occurred
        context: Additional context about the error

    Returns:
        The log entry data
    """
    return {
        "task_id": task_id,
        "config_id": config_id,
        "instance_id": instance_id,
        "status": ManualTaskLogStatus.error,
        "message": str(error),
        "details": context,
    }
