from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from loguru import logger
from pydantic import ValidationError

from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_config import ManualTaskFieldBase
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus
from fides.api.schemas.manual_tasks.manual_task_status import StatusType

T = TypeVar("T")


def validate_fields(fields: list[dict[str, Any]], is_submission: bool = False) -> None:
    """Validate field data against the appropriate Pydantic model.

    Args:
        fields: List of field data to validate
        is_submission: Whether the fields are for a submission (True) or configuration (False)

    Raises:
        ValueError: If the field data is invalid
    """
    # Check for duplicate field keys
    field_keys = {str(field.get("field_key")): field for field in fields}
    if len(field_keys) != len(fields):
        raise ValueError(
            "Duplicate field keys found in field updates, field keys must be unique."
        )

    for field in fields:
        try:
            _validate_field(field, is_submission)
        except ValidationError as e:
            raise ValueError(f"Invalid field data: {str(e)}")
        except ValueError as e:
            raise ValueError(str(e))


def _validate_field(field: dict[str, Any], is_submission: bool = False) -> None:
    """Validate a field.

    Args:
        field: The field to validate
        is_submission: Whether the field is a submission field

    Raises:
        ValueError: If the field data is invalid
    """
    if not field.get("field_key"):
        raise ValueError("Invalid field data: field_key is required")

    if not field.get("field_type"):
        raise ValueError("Invalid field data: field_type is required")

    if is_submission and "value" not in field:
        raise ValueError("Invalid field data: value is required for submissions")
    if not is_submission:
        field_model = ManualTaskFieldBase.get_field_model_for_type(field["field_type"])
        field_model.model_validate(field)


class TaskLogger:
    """Class-based decorator for logging operation success/failure in service methods.
    Args:
        operation_name: The name of the operation to log
        success_status: The status to log for successful operations

    The decorated function can return either:
    - A tuple of (return_value, log_details)
    - Just the return value (in which case log details will be extracted from it)
    """

    def __init__(
        self,
        operation_name: str,
        success_status: ManualTaskLogStatus = ManualTaskLogStatus.complete,
    ) -> None:
        self.operation_name = operation_name
        self.success_status = success_status

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapped(service_self: Any, *args: Any, **kwargs: Any) -> T:
            try:
                result = func(service_self, *args, **kwargs)

                # Handle tuple returns (return_value, log_details)
                if isinstance(result, tuple) and len(result) == 2:
                    return_value, log_details = result
                    log_data = self._create_log_data(return_value, kwargs)
                    if isinstance(log_details, dict):
                        log_data.update(log_details)
                else:
                    # Create log data from the result
                    log_data = self._create_log_data(result, kwargs)
                    return_value = result

                self._log_success(service_self, log_data)
                return return_value
            except Exception as e:
                self._log_error(service_self, e, kwargs)
                raise

        return wrapped

    def _create_log_data(self, result: Any, kwargs: dict) -> dict:
        """Create log data from result or kwargs."""
        log_data = {}

        # Handle all ID fields uniformly
        id_fields = ["task_id", "config_id", "instance_id"]
        for field in id_fields:
            # Get from result if available, otherwise from kwargs
            log_data[field] = getattr(result, field, None) or kwargs.get(field)

        # Add any additional details
        log_data["details"] = kwargs.get("details", {})

        return log_data

    def _create_base_log_data(self, data: dict) -> dict:
        """Extract common log data from input dictionary."""
        return {
            "task_id": data.get("task_id"),
            "config_id": data.get("config_id"),
            "instance_id": data.get("instance_id"),
            "details": data.get("details", {}),
        }

    def _log_success(self, service_self: Any, log_data: dict) -> None:
        """Log successful operation execution."""
        if not hasattr(service_self, "db") or not log_data.get("task_id"):
            return

        ManualTaskLog.create_log(
            db=service_self.db,
            **self._create_base_log_data(log_data),
            status=self.success_status,
            message=self.operation_name,
        )

    def _log_error(self, service_self: Any, error: Exception, kwargs: dict) -> None:
        """Log operation error."""
        logger.error(f"Error in {self.operation_name}: {str(error)}")
        logger.error(f"Error details: {kwargs.get('details', {})}")

        if not hasattr(service_self, "db") or not kwargs.get("task_id"):
            return

        ManualTaskLog.create_log(
            db=service_self.db,
            **self._create_base_log_data(kwargs),
            status=ManualTaskLogStatus.error,
            message=f"Error in {self.operation_name}: {str(error)}",
        )

    @staticmethod
    def log_status_change(
        db: Any,
        task_id: str,
        config_id: Optional[str],
        instance_id: Optional[str],
        previous_status: StatusType,
        new_status: StatusType,
        user_id: Optional[str] = None,
    ) -> None:
        """Log a status change event.

        Args:
            db: Database connection
            task_id: The task ID
            config_id: The config ID
            instance_id: The instance ID
            previous_status: The previous status
            new_status: The new status
            user_id: The user ID making the change
        """
        ManualTaskLog.create_log(
            db=db,
            task_id=task_id,
            config_id=config_id,
            instance_id=instance_id,
            status=ManualTaskLogStatus.in_progress,
            message=f"Task instance status transitioning from {previous_status} to {new_status}",
            details={
                "previous_status": previous_status,
                "new_status": new_status,
                "user_id": user_id,
            },
        )

    @staticmethod
    def log_create(
        db: Any,
        task_id: str,
        entity_type: str,
        entity_id: str,
        details: Optional[dict] = None,
        user_id: Optional[str] = None,
        status: ManualTaskLogStatus = ManualTaskLogStatus.created,
    ) -> None:
        """Log a creation event for a task, config, instance, or submission.

        Args:
            db: Database connection
            task_id: The task ID
            entity_type: Type of entity being created (e.g., 'task', 'config', 'instance', 'submission')
            entity_id: ID of the created entity
            details: Additional details about the creation
            user_id: The user ID performing the creation
            status: Status to use for the log entry (defaults to created)
        """
        # Map entity type to the appropriate ID field
        id_fields = {
            "task": {"task_id": task_id},
            "config": {"task_id": task_id, "config_id": entity_id},
            "instance": {"task_id": task_id, "instance_id": entity_id},
            "submission": {"task_id": task_id, "instance_id": entity_id},
        }

        if entity_type not in id_fields:
            raise ValueError(f"Invalid entity type: {entity_type}")

        log_details = details or {}
        if user_id is not None:
            log_details["user_id"] = user_id

        ManualTaskLog.create_log(
            db=db,
            **id_fields[entity_type],
            status=status,
            message=f"Created new {entity_type}",
            details=log_details,
        )


# Alias the class to maintain the original decorator name
with_task_logging = TaskLogger
