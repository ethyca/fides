"""RBAC Role Constraint model for separation of duties and cardinality constraints."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base

if TYPE_CHECKING:
    from fides.api.models.rbac.rbac_role import RBACRole


class ConstraintType(str, Enum):
    """Types of RBAC constraints."""

    STATIC_SOD = "static_sod"
    """
    Static Separation of Duties: Users cannot be assigned both roles simultaneously.
    Checked at role assignment time.
    """

    DYNAMIC_SOD = "dynamic_sod"
    """
    Dynamic Separation of Duties: Users cannot activate both roles in the same session.
    Checked at runtime/permission evaluation time.
    """

    CARDINALITY = "cardinality"
    """
    Cardinality constraint: Limits the number of users that can be assigned a role.
    """


class RBACRoleConstraint(Base):
    """
    Separation of duties and cardinality constraints for RBAC.

    Constraints enforce security policies:
    - Static SoD: Prevents users from holding conflicting roles
    - Dynamic SoD: Prevents users from using conflicting roles in same session
    - Cardinality: Limits how many users can have a role

    Examples:
    - Static SoD: approver and contributor cannot be held by same user
    - Cardinality: Only 3 users can be owners
    """

    __tablename__ = "rbac_role_constraint"

    name = Column(
        String(255),
        nullable=False,
        comment="Human-readable name for this constraint",
    )
    constraint_type = Column(
        String(50),
        nullable=False,
        comment="Type of constraint: static_sod, dynamic_sod, or cardinality",
    )
    role_id_1 = Column(
        String(255),
        ForeignKey("rbac_role.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="First role in the constraint (required for all types)",
    )
    role_id_2 = Column(
        String(255),
        ForeignKey("rbac_role.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Second role in the constraint (required for SoD, NULL for cardinality)",
    )
    max_users = Column(
        Integer,
        nullable=True,
        comment="Maximum number of users for cardinality constraint",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Description of why this constraint exists",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Whether this constraint is currently enforced",
    )

    # Relationships
    role_1: "RBACRole" = relationship(
        "RBACRole",
        foreign_keys=[role_id_1],
        lazy="selectin",
    )
    role_2: Optional["RBACRole"] = relationship(
        "RBACRole",
        foreign_keys=[role_id_2],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        if self.constraint_type == ConstraintType.CARDINALITY:
            return f"<RBACRoleConstraint(type='{self.constraint_type}', role='{self.role_id_1}', max={self.max_users})>"
        return f"<RBACRoleConstraint(type='{self.constraint_type}', roles='{self.role_id_1}' <-> '{self.role_id_2}')>"

    def is_sod_constraint(self) -> bool:
        """Check if this is a separation of duties constraint."""
        return self.constraint_type in (
            ConstraintType.STATIC_SOD,
            ConstraintType.DYNAMIC_SOD,
        )

    def is_cardinality_constraint(self) -> bool:
        """Check if this is a cardinality constraint."""
        return self.constraint_type == ConstraintType.CARDINALITY

    def involves_role(self, role_id: str) -> bool:
        """Check if a role is involved in this constraint."""
        return role_id in (self.role_id_1, self.role_id_2)

    def get_conflicting_role_id(self, role_id: str) -> Optional[str]:
        """
        For SoD constraints, get the role that conflicts with the given role.

        Args:
            role_id: The role to check

        Returns:
            The conflicting role ID, or None if not a SoD constraint or role not involved
        """
        if not self.is_sod_constraint():
            return None

        if role_id == self.role_id_1:
            return self.role_id_2
        if role_id == self.role_id_2:
            return self.role_id_1
        return None
