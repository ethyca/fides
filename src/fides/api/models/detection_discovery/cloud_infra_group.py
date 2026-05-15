from __future__ import annotations

from typing import Any

from loguru import logger
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    event,
    func,
    select,
    text,
    update,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.detection_discovery.cloud_infra import CloudInfraStagedResource
from fides.api.models.sql_models import System  # type: ignore[attr-defined]


class CloudInfraGroup(Base):
    """
    A named logical collection of cloud infra resources that maps to a System.

    A group can target a new System (system_id is NULL, name holds the
    intended System name — system_id is set on first promotion when the
    System is created) or an existing System (system_id set at group creation).

    Resources are linked via CloudInfraGroupAssignment (many-to-many).
    """

    @declared_attr
    def __tablename__(self) -> str:  # type: ignore[override]
        return "cloud_infra_group"

    monitor_config_id = Column(String, nullable=False, index=True)
    # Nullable — groups without a linked System use this as a draft label;
    # groups linked to a System may leave it NULL
    name = Column(String, nullable=True)
    # No ondelete: _unlink_groups_on_system_delete (below) clears system_id
    # and resets promoted assignments before the FK constraint fires.
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

    @classmethod
    def create(cls, db: Session, *, data: dict) -> "CloudInfraGroup":  # type: ignore[override]
        return super().create(db=db, data=data, check_name=False)

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
    resource = relationship(
        "CloudInfraStagedResource",
    )

    __table_args__ = (
        UniqueConstraint(
            "resource_id",
            "group_id",
            name="uq_cloud_infra_group_assignment",
        ),
    )


@event.listens_for(System, "before_delete")
def _unlink_groups_on_system_delete(
    mapper: Any, connection: Any, target: System
) -> None:
    """Revert groups to draft and reset promoted assignments before a System is deleted.

    When a System is deleted:
    1. Reset ``promoted = false`` on all assignments for affected groups.
    2. Revert ``diff_status`` to ``addition`` on resources that no longer have
       any promoted assignment in *any* group.
    3. Clear ``system_id`` on affected groups (revert to draft).
    """
    group_table = CloudInfraGroup.__table__
    assignment_table = CloudInfraGroupAssignment.__table__

    # IDs of groups targeting the deleted System
    affected_group_ids = select(group_table.c.id).where(  # type: ignore[arg-type]
        group_table.c.system_id == target.id
    )

    # Materialize promoted resource IDs *before* resetting promoted flags,
    # otherwise the lazy subquery would see the already-reset rows.
    affected_resource_ids = [
        row[0]
        for row in connection.execute(
            select(assignment_table.c.resource_id)  # type: ignore[arg-type]
            .where(assignment_table.c.group_id.in_(affected_group_ids))
            .where(assignment_table.c.promoted == True)  # noqa: E712
        ).all()
    ]

    logger.debug(
        "Unlinking cloud infra groups from System {} before deletion", target.id
    )

    # 1. Reset promoted on assignments for affected groups
    connection.execute(
        update(assignment_table)
        .where(assignment_table.c.group_id.in_(affected_group_ids))
        .values(promoted=False)
    )

    # 2. Revert diff_status on resources that now have zero promoted assignments
    if affected_resource_ids:
        resource_table = CloudInfraStagedResource.__table__

        still_promoted = (
            select(assignment_table.c.resource_id)  # type: ignore[arg-type]
            .where(assignment_table.c.resource_id.in_(affected_resource_ids))
            .where(assignment_table.c.promoted == True)  # noqa: E712
        )

        connection.execute(
            update(resource_table)
            .where(resource_table.c.id.in_(affected_resource_ids))
            .where(resource_table.c.id.notin_(still_promoted))
            .values(diff_status="addition")
        )

    # 3. Clear system_id on affected groups (revert to draft).
    #    Preserve the System name as the group name so users can see
    #    what the group was targeting before the System was deleted.
    connection.execute(
        update(group_table)
        .where(group_table.c.system_id == target.id)
        .values(
            system_id=None,
            name=func.coalesce(group_table.c.name, target.name),
        )
    )
