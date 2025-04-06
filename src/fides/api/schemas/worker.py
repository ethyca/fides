from datetime import datetime
from typing import Any, Dict, List, Optional

from fides.api.schemas.base_class import FidesSchema


class TaskDetails(FidesSchema):
    task_id: str
    task_name: str
    args: List[Any]
    keyword_args: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None

    @classmethod
    def from_celery_task(cls, task: dict, state: str) -> "TaskDetails":
        timestamp = (
            datetime.fromtimestamp(task["time_start"]).isoformat()
            if task.get("time_start")
            else None
        )

        # Only include kwargs for execute request tasks
        keyword_args = None
        if any(
            task_type in task["name"]
            for task_type in ["run_access_node", "run_erasure_node", "run_consent_node"]
        ):
            keyword_args = task.get("kwargs", {})

        return cls(
            task_id=task["id"],
            task_name=task["name"],
            args=task.get("args", []),
            keyword_args=keyword_args,
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
