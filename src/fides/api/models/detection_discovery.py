from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Type

from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base, FidesBase
from fides.api.models.connectionconfig import ConnectionConfig

# class MonitorExecution(BaseModel):
#     id: str
#     monitor_config_id: str
#     status: Optional[str]
#     started: Optional[datetime]
#     completed: Optional[datetime]
#     classification_instances: List[str] = PydanticField(
#         default_factory=list
#     )  # TODO: formalize to FK


class DiffStatus(Enum):
    ADDITION = "addition"
    REMOVAL = "removal"
    CLASSIFICATION_ADDITION = "classification_addition"
    CLASSIFICATION_UPDATE = "classification_update"
    MONITORED = "monitored"
    MUTED = "muted"


class MonitorFrequency(Enum):
    """
    Enum representing monitor frequency. Not used in DB but needed for translating to API schema
    """

    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"


class MonitorConfig(Base):
    """
    Monitor configuration used for data detection and discovery.

    Each monitor configuration references `ConnectionConfig`, which provide it with underlying
    configuration details used in connecting to the external data store.
    """

    name = Column(String, nullable=True)
    key = Column(String, index=True, unique=True, nullable=False)
    connection_config_id = Column(
        String,
        ForeignKey(ConnectionConfig.id_field_path),
        nullable=False,
        index=True,
    )
    databases = Column(
        ARRAY(String),
        index=False,
        unique=False,
        nullable=False,
        server_default="{}",
        default=dict,
    )  # the databases to which the monitor is scoped
    monitor_execution_trigger = Column(
        MutableDict.as_mutable(JSONB),
        index=False,
        unique=False,
        nullable=True,
    )  # stores the cron-based kwargs for scheduling the monitor execution.
    # see https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html

    classify_params = Column(
        MutableDict.as_mutable(JSONB), index=False, unique=False, nullable=True
    )  # parameters that the monitor will use for classification execution

    # TODO: many-to-many link to users assigned as data stewards; likely will need a join-table

    connection_config = relationship(ConnectionConfig)

    @property
    def connection_config_key(self) -> str:
        """Derives the `connection_config_key`"""
        return self.connection_config.key

    @property
    def execution_start_date(self) -> Optional[datetime]:
        """Derives the `execution_start_date`"""
        if (
            not self.monitor_execution_trigger
            or not self.monitor_execution_trigger.get("start_date")
        ):
            return None
        return self.monitor_execution_trigger.get("start_date")

    @property
    def execution_frequency(self) -> Optional[MonitorFrequency]:
        """Derives the `execution_frequency`"""
        if (
            not self.monitor_execution_trigger
            or not self.monitor_execution_trigger.get("hour")
        ):
            return None
        if self.monitor_execution_trigger.get("day"):
            return MonitorFrequency.MONTHLY
        if self.monitor_execution_trigger.get("day_of_week"):
            return MonitorFrequency.WEEKLY
        return MonitorFrequency.DAILY

    def update(self, db: Session, *, data: dict[str, Any]) -> FidesBase:
        """Override the base class `update` to derive the `execution_trigger` dict field"""
        MonitorConfig.derive_execution_trigger_dict(data)
        return super().update(db=db, data=data)

    @classmethod
    def create(
        cls: Type[MonitorConfig],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = True,
    ) -> MonitorConfig:
        """Override the base class `create` to derive the `execution_trigger` dict field"""
        MonitorConfig.derive_execution_trigger_dict(data)
        return super().create(db=db, data=data, check_name=check_name)

    @staticmethod
    def derive_execution_trigger_dict(data: Dict[str, Any]) -> None:
        """
        Determines the execution trigger (cron) dict based on the
        corresponding schema properties provided in the `data` dict.

        The `data` dict is updated in place with the execution trigger dict
        placed in the `monitor_execution_trigger` key, if applicable, and with the
        `execution_frequency` and `execution_start_date` keys removed.

        The `execution_start_date` is inferred as the basis for the day and time
        for repeated monitor execution, and the frequency of execution is based
        on the `execution_frequency` field.

        For example, an `execution_start_date` of "2024-05-14 12:00:00+00:00":
        - with an `execution_frequency` of "daily", it will result in daily
        execution at 12:00:00+00:00;
        - with an `execution_frequency` of "weekly", it will result in weekly
        execution at 12:00:00+00:00 on every Tuesday, since 2024-05-14 is
        a Tuesday.
        - with an `execution_frequency` of "monthly", it will result in monthly
        execution at 12:00:00+00:00 on the 14th day of every month.

        See https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html
        for more information about the cron trigger parameters.
        """
        execution_frequency = data.pop("execution_frequency", None)
        execution_start_date = data.pop("execution_start_date", None)
        if execution_frequency and execution_start_date:
            cron_trigger_dict = {}
            cron_trigger_dict["start_date"] = execution_start_date
            cron_trigger_dict["timezone"] = execution_start_date.tzinfo
            cron_trigger_dict["hour"] = execution_start_date.hour
            cron_trigger_dict["minute"] = execution_start_date.minute
            cron_trigger_dict["second"] = execution_start_date.second
            if execution_frequency == MonitorFrequency.WEEKLY:
                cron_trigger_dict["day_of_week"] = execution_start_date.weekday()
            if execution_frequency == MonitorFrequency.MONTHLY:
                cron_trigger_dict["day"] = execution_start_date.day
            data["monitor_execution_trigger"] = cron_trigger_dict


class StagedResource(Base):
    """
    Base DB model that represents a staged resource, fields common to all types of staged resources
    """

    name = Column(String, nullable=True)
    urn = Column(String, index=True, unique=True, nullable=False)
    resource_type = Column(String, index=True, nullable=True)
    description = Column(String, nullable=True)
    monitor_config_id = Column(String, nullable=True)  # just a "soft" pointer, for now
    source_modified = Column(
        DateTime(timezone=True),
        nullable=True,
    )  # when the table was modified in the datasource
    classifications = Column(
        ARRAY(JSONB),
        nullable=False,
        server_default="{}",
        default=dict,
    )
    user_assigned_data_categories = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
        default=dict,
    )

    # pointers to child and parent URNs
    children = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
        default=dict,
    )
    parent = Column(String, nullable=True)

    # diff-related fields
    diff_status = Column(String, nullable=True)
    child_diff_statuses = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        server_default="{}",
        default=dict,
    )

    # placeholder for additional attributes
    meta = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        server_default="{}",
        default=dict,
    )

    @classmethod
    def get_urn(cls, db: Session, urn: str) -> Optional[StagedResource]:
        """Utility to retrieve the staged resource with the given URN"""
        return cls.get_by(db=db, field="urn", value=urn)

    def add_child_diff_status(self, diff_status: DiffStatus) -> None:
        """Increments the specified child diff status"""
        self.child_diff_statuses[diff_status.value] = (
            self.child_diff_statuses.get(diff_status.value, 0) + 1
        )

    def mark_as_addition(
        self,
        db: Session,
        parent_resource_urns: Iterable[str] = [],
    ) -> None:
        """
        Marks the resource as an addition and the child diff status of
        the given parent resource URNs accordingly
        """
        self.diff_status = DiffStatus.ADDITION.value
        for parent_resource_urn in parent_resource_urns:
            parent_resource: Optional[StagedResource] = StagedResource.get_urn(
                db, parent_resource_urn
            )
            if parent_resource:
                parent_resource.add_child_diff_status(DiffStatus.ADDITION)
