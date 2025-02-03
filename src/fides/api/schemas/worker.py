from datetime import datetime
from typing import Any, Dict, List, Optional
from fides.api.schemas.base_class import FidesSchema


class TaskDetails(FidesSchema):
    task_id: str
    task_name: str
    args: List[Any]
    kwargs: Dict[str, Any]
    started_at: Optional[str] = None

    @classmethod
    def from_celery_task(cls, task: dict, state: str) -> "TaskDetails":
        # Handle cases where time_start might be None
        timestamp = None
        if task.get("time_start"):
            try:
                timestamp = datetime.fromtimestamp(task["time_start"]).isoformat()
            except (TypeError, ValueError):
                timestamp = None

        return cls(
            task_id=task["id"],
            task_name=task["name"],
            args=task.get("args", []),
            kwargs=task.get("kwargs", {}),
            started_at=timestamp,
            state=state,
        )


class WorkerInfo(FidesSchema):
    active_task: Optional[TaskDetails] = None
    reserved_tasks: List[TaskDetails] = []
    registered_tasks: List[str] = []


class QueueInfo(FidesSchema):
    messages: int


class WorkerStats(FidesSchema):
    queues: Dict[str, QueueInfo]
    workers: Dict[str, WorkerInfo]
