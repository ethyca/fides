from __future__ import annotations

from enum import Enum
from typing import List, Optional

from sqlalchemy import ARRAY, Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base, FidesBase  # type: ignore[attr-defined]
from fides.api.models.detection_discovery.core import MonitorConfig
from fides.api.models.worker_task import (
    ExecutionLogStatus,
    TaskExecutionLog,
    WorkerTask,
)


class MonitorTaskType(Enum):
    """
    Types of tasks that can be executed by a worker.
    """

    DETECTION = "detection"
    CLASSIFICATION = "classification"
    PROMOTION = "promotion"
    REMOVAL_PROMOTION = "removal_promotion"


class MonitorTask(WorkerTask, Base):
    """
    A monitor task executed by a worker.
    """

    # celery_id is used to track task executions. While MonitorTask.id remains constant,
    # celery_id changes with each execution or retry of the task, allowing us to track
    # the current execution state while maintaining a stable reference to the original task.
    celery_id = Column(
        String(255), unique=True, nullable=False, default=FidesBase.generate_uuid
    )
    task_arguments = Column(JSONB, nullable=True)  # To be able to rerun the task
    # Contains info, warning, or error messages
    message = Column(String)
    monitor_config_id = Column(
        String,
        ForeignKey(MonitorConfig.id_field_path, ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    staged_resource_urns = Column(ARRAY(String), nullable=True)
    child_resource_urns = Column(ARRAY(String), nullable=True)

    monitor_config = relationship(MonitorConfig, cascade="all, delete")
    execution_logs = relationship(
        "MonitorTaskExecutionLog", back_populates="monitor_task", cascade="all, delete"
    )

    @classmethod
    def allowed_action_types(cls) -> List[str]:
        return [e.value for e in MonitorTaskType]


class TaskRunType(Enum):
    """
    Type of task run.
    """

    MANUAL = "manual"
    SYSTEM = "system"


class MonitorTaskExecutionLog(TaskExecutionLog, Base):
    """
    Stores the individual execution logs associated with a MonitorTask.
    """

    # This celery_id preserves the specific execution ID for historical tracking,
    # unlike MonitorTask.celery_id which is updated with each execution.
    # This allows us to maintain a complete history of all task execution attempts.
    celery_id = Column(String(255), nullable=False)
    monitor_task_id = Column(
        String,
        ForeignKey(MonitorTask.id_field_path, ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    run_type = Column(
        SQLAlchemyEnum(TaskRunType), nullable=False, default=TaskRunType.SYSTEM
    )

    monitor_task = relationship("MonitorTask", back_populates="execution_logs")


def create_monitor_task_with_execution_log(
    db: Session, monitor_task_data: dict
) -> MonitorTask:
    """
    Creates a monitor task with an execution log.
    The default status is pending for the task and pending for the execution log.
    """
    status = ExecutionLogStatus.pending
    task_record = MonitorTask(  # type: ignore
        status=status.value,
        **monitor_task_data,
    )
    db.add(task_record)
    db.flush()

    execution_log = MonitorTaskExecutionLog(  # type: ignore
        monitor_task=task_record, celery_id=task_record.celery_id, status=status
    )
    db.add(execution_log)

    db.commit()
    db.refresh(task_record)
    return task_record


def update_monitor_task_with_execution_log(
    db: Session,
    status: ExecutionLogStatus,
    task_record: Optional[MonitorTask] = None,
    celery_id: Optional[str] = None,
    message: Optional[str] = None,
    run_type: TaskRunType = TaskRunType.SYSTEM,
) -> MonitorTask:
    """
    Updates a monitor task with an execution log.

    It must be either celery_id or task_record. If it doesn't receive a celery_id, it's assumed a new one needs to be created because a new run is about to be performed.
    If it receives a celery_id, it means it only needs to update the status of an existing run. It can receive task_record to avoid querying the database again to get it.
    """
    if not celery_id and not task_record:
        raise ValueError("Either celery_id or task_record must be provided")

    if celery_id and not task_record:
        task_record = MonitorTask.get_by(db=db, field="celery_id", value=celery_id)
        if not task_record:
            raise ValueError(f"Could not find MonitorTask with celery_id {celery_id}")

    assert task_record is not None  # help type checker understand the control flow

    if not celery_id:
        celery_id = task_record.generate_uuid()
        task_record.celery_id = celery_id

    task_record.status = status.value  # type: ignore
    task_record.message = message

    MonitorTaskExecutionLog(  # type: ignore
        monitor_task=task_record,
        status=status,
        message=message,
        celery_id=celery_id,
        run_type=run_type,
    )

    db.commit()
    db.refresh(task_record)
    return task_record
