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
    if len({str(field.get("field_key")) for field in fields}) != len(fields):
        raise ValueError(
            "Duplicate field keys found in field updates, field keys must be unique."
        )

    for field in fields:
        if not field.get("field_key"):
            raise ValueError("Invalid field data: field_key is required")
        if not field.get("field_type"):
            raise ValueError("Invalid field data: field_type is required")
        if is_submission and "value" not in field:
            raise ValueError("Invalid field data: value is required for submissions")
        if not is_submission:
            try:
                field_model = ManualTaskFieldBase.get_field_model_for_type(
                    field["field_type"]
                )
                field_model.model_validate(field)
            except ValidationError as e:
                raise ValueError(f"Invalid field data: {str(e)}")


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
                return_value, log_data = (
                    result
                    if isinstance(result, tuple) and len(result) == 2
                    else (result, {})
                )
                if hasattr(service_self, "db") and (
                    task_id := self._get_task_id(return_value, kwargs)
                ):
                    self._log_success(
                        service_self.db, task_id, return_value, log_data, kwargs
                    )
                return return_value
            except Exception as e:
                self._log_error(service_self, e, kwargs)
                raise

        return wrapped

    def _get_task_id(self, result: Any, kwargs: dict) -> Optional[str]:
        """Extract task_id from result or kwargs."""
        return getattr(result, "task_id", None) or kwargs.get("task_id")

    def _get_log_data(self, result: Any, kwargs: dict) -> dict:
        """Create log data from result and kwargs."""
        log_data = {}
        for field in ["task_id", "config_id", "instance_id"]:
            if value := getattr(result, field, None) or kwargs.get(field):
                log_data[field] = value
        log_data["details"] = kwargs.get("details", {})
        return log_data

    def _log_success(
        self, db: Any, task_id: str, result: Any, log_data: dict, kwargs: dict
    ) -> None:
        """Log successful operation."""
        ManualTaskLog.create_log(
            db=db,
            **self._get_log_data(result, kwargs | log_data),
            status=self.success_status,
            message=self.operation_name,
        )

    def _log_error(self, service_self: Any, error: Exception, kwargs: dict) -> None:
        """Log operation error."""
        logger.error(f"Error in {self.operation_name}: {str(error)}")
        if hasattr(service_self, "db") and (task_id := self._get_task_id({}, kwargs)):
            ManualTaskLog.create_log(
                db=service_self.db,
                task_id=task_id,
                **{
                    k: v
                    for k, v in self._get_log_data({}, kwargs).items()
                    if k != "task_id"
                },
                status=ManualTaskLogStatus.error,
                message=f"Error in {self.operation_name}: {str(error)}",
            )

    @staticmethod
    def log_status_change(
        db: Any,
        task_id: str,
        config_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        previous_status: Optional[StatusType] = None,
        new_status: Optional[StatusType] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Log a status change event."""
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
        """Log a creation event."""
        id_fields = {
            "task": {"task_id": task_id},
            "config": {"task_id": task_id, "config_id": entity_id},
            "instance": {"task_id": task_id, "instance_id": entity_id},
            "submission": {"task_id": task_id, "instance_id": entity_id},
        }
        if entity_type not in id_fields:
            raise ValueError(f"Invalid entity type: {entity_type}")

        ManualTaskLog.create_log(
            db=db,
            **id_fields[entity_type],
            status=status,
            message=f"Created new {entity_type}",
            details=(details or {}) | ({"user_id": user_id} if user_id else {}),
        )


# Alias the class to maintain the original decorator name
with_task_logging = TaskLogger
