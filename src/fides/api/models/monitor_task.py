import enum
from typing import List

from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from fides.api.db.base_class import Base
from fides.api.models.detection_discovery import MonitorConfig
from fides.api.models.worker_task import TaskExecutionLog, WorkerTask


class MonitorTaskType(enum.Enum):
    """
    Types of tasks that can be executed by a worker.
    """

    DETECTION = "detection"
    CLASSIFICATION = "classification"
    PROMOTION = "promotion"


class MonitorTask(WorkerTask, Base):
    """
    A monitor task executed by a worker.
    """

    celery_id = Column(String, unique=True, nullable=False)
    task_arguments = Column(JSONB, nullable=True)  # To be able to rerun the task
    # Contains info, warning, or error messages
    message = Column(String)
    monitor_config_id = Column(
        String, ForeignKey(MonitorConfig.id_field_path), nullable=False
    )
    staged_resource_urn = Column(String, nullable=False)
    child_resource_urns = Column(ARRAY(String), nullable=True)

    @classmethod
    def allowed_action_types(cls) -> List[str]:
        return [e.value for e in MonitorTaskType]


class TaskRunType(enum.Enum):
    """
    Type of task run.
    """

    MANUAL = "manual"
    SYSTEM = "system"


class MonitorTaskExecutionLog(TaskExecutionLog, Base):
    """
    Stores the individual execution logs associated with a MonitorTask.
    """

    celery_id = Column(String, unique=True, nullable=False)
    monitor_task_id = Column(
        String, ForeignKey(MonitorTask.id_field_path), index=True, nullable=False
    )
    run_type = Column(Enum(TaskRunType), nullable=False, default=TaskRunType.SYSTEM)
