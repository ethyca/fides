from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base


class CloudInfraGroup(Base):
    """
    A named logical collection of cloud infra resources that maps to a System.

    A group can target a new System (system_id is NULL, draft_system_name holds
    the intended name — system_id is set on first promotion when the System is
    created) or an existing System (system_id set at group creation).

    Resources are linked via CloudInfraGroupAssignment (many-to-many).
    """

    @declared_attr
    def __tablename__(self) -> str:  # type: ignore[override]
        return "cloud_infra_group"

    monitor_config_id = Column(String, nullable=False, index=True)
    draft_system_name = Column(String, nullable=True)
    system_id = Column(
        String,
        ForeignKey("ctl_systems.id"),
        nullable=True,
        index=True,
    )

    assignments = relationship(
        "CloudInfraGroupAssignment",
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # A System can only have one group per monitor. Groups from different
        # monitors can target the same System. Only enforced when system_id is
        # set (partial unique index).
        Index(
            "ix_cloud_infra_group_monitor_system_unique",
            "monitor_config_id",
            "system_id",
            unique=True,
            postgresql_where=text("system_id IS NOT NULL"),
        ),
    )


class CloudInfraGroupAssignment(Base):
    """
    Join table linking cloud infra resources to groups (many-to-many).

    A resource can belong to multiple groups. The ``promoted`` flag tracks
    whether the resource has been promoted within this specific group — a
    resource can be promoted in one group but not yet in another.
    """

    @declared_attr
    def __tablename__(self) -> str:  # type: ignore[override]
        return "cloud_infra_group_assignment"

    resource_id = Column(
        String(255),
        ForeignKey("cloud_infra_staged_resource.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    group_id = Column(
        String(255),
        ForeignKey("cloud_infra_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    promoted = Column(Boolean, nullable=False, default=False, server_default="false")

    group = relationship(
        "CloudInfraGroup",
        back_populates="assignments",
    )

    __table_args__ = (
        UniqueConstraint(
            "resource_id",
            "group_id",
            name="uq_cloud_infra_group_assignment",
        ),
    )
