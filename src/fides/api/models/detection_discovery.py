from __future__ import annotations

from enum import Enum
from typing import Iterable

from sqlalchemy import ARRAY, Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base

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


class StagedResource(Base):
    """
    Base DB model that represents a staged resource, fields common to all types of staged resources
    """

    name = Column(String, nullable=False)
    urn = Column(String, index=True, unique=True, nullable=False)
    resource_type = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    monitor_config_id = Column(String, nullable=False)  # just a "soft" pointer, for now
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
    def get_urn(cls, db: Session, urn: str):
        return cls.get_by(db=db, field="urn", value=urn)

    def add_child_diff_status(self, diff_status: DiffStatus):
        self.child_diff_statuses[diff_status.value] = (
            self.child_diff_statuses.get(diff_status.value, 0) + 1
        )

    def mark_as_addition(
        self,
        db: Session,
        parent_resource_urns: Iterable[str] = [],
    ) -> None:
        self.diff_status = DiffStatus.ADDITION.value
        for parent_resource_urn in parent_resource_urns:
            parent_resource: StagedResource = StagedResource.get_urn(
                db, parent_resource_urn
            )
            parent_resource.add_child_diff_status(DiffStatus.ADDITION.value)
