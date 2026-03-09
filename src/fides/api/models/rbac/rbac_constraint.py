"""RBAC Constraint model for separation of duties and cardinality constraints.

Implements constraint types from the NIST RBAC standard (ANSI/INCITS 359-2004):
- Static SoD: SSD(role_set, n) — no user may be assigned to n or more roles in role_set
- Dynamic SoD: DSD(role_set, n) — no user may activate n or more roles in role_set per session
- Cardinality: limits the maximum number of users that can hold any role in the set

See: https://csrc.nist.gov/projects/role-based-access-control
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty, relationship

from fides.api.db.base_class import Base

if TYPE_CHECKING:
    from fides.api.models.rbac.rbac_role import RBACRole


class ConstraintType(str, Enum):
    """
    Types of RBAC constraints as defined by the NIST RBAC standard (ANSI/INCITS 359-2004).
    """

    STATIC_SOD = "static_sod"
    """
    Static Separation of Duties — SSD(role_set, n):
    No user may be assigned to n or more roles from the role_set.
    Checked at role assignment time.
    """

    DYNAMIC_SOD = "dynamic_sod"
    """
    Dynamic Separation of Duties — DSD(role_set, n):
    No user may activate n or more roles from the role_set in a single session.
    Users may hold all roles in the set, but cannot use n or more simultaneously.
    Checked at runtime/session activation time.
    """

    CARDINALITY = "cardinality"
    """
    Cardinality constraint:
    Limits the maximum number of users that can be assigned to any role in the set.
    The threshold value represents the maximum number of users allowed.
    """


class RBACConstraint(Base):
    """
    RBAC constraint definition following the NIST RBAC standard (ANSI/INCITS 359-2004).

    Constraints enforce security policies over sets of roles:
    - Static SoD (SSD): Prevents users from being assigned too many roles from
      a conflicting set. Defined as SSD(role_set, n) where n is the threshold.
    - Dynamic SoD (DSD): Prevents users from activating too many roles from a
      conflicting set in the same session. Defined as DSD(role_set, n).
    - Cardinality: Limits how many users can hold any role in the set. The
      threshold represents the maximum number of users allowed.

    The roles in the constraint set are linked via the rbac_constraint_role
    junction table, allowing constraints over arbitrary sets of roles (not
    just pairs).

    Examples:
    - SSD({contributor, approver}, 2): user cannot hold both roles
    - SSD({admin, auditor, operator}, 2): user can hold at most 1 of the 3
    - DSD({manager, reviewer}, 2): user can hold both but not use both per session
    - Cardinality({owner}, 3): at most 3 users can be owners
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "rbac_constraint"

    name = Column(
        String(255),
        nullable=False,
        comment="Human-readable name for this constraint",
    )
    constraint_type = Column(
        String(50),
        nullable=False,
        comment="Type of constraint: static_sod, dynamic_sod, or cardinality (per NIST RBAC)",
    )
    threshold = Column(
        Integer,
        nullable=False,
        comment=(
            "NIST 'n' value. For SoD: max roles from set a user can hold/activate "
            "(e.g. 2 = mutual exclusion for a 2-role set). "
            "For cardinality: max users that can hold any role in the set."
        ),
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

    # Roles in this constraint's role set, linked via junction table
    roles: RelationshipProperty[List["RBACRole"]] = relationship(
        "RBACRole",
        secondary="rbac_constraint_role",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        role_count = len(self.roles) if self.roles else 0
        return (
            f"<RBACConstraint(name='{self.name}', type='{self.constraint_type}', "
            f"roles={role_count}, threshold={self.threshold})>"
        )

    def is_sod_constraint(self) -> bool:
        """Check if this is a separation of duties constraint (static or dynamic)."""
        return self.constraint_type in (
            ConstraintType.STATIC_SOD,
            ConstraintType.DYNAMIC_SOD,
        )

    def is_cardinality_constraint(self) -> bool:
        """Check if this is a cardinality constraint."""
        return self.constraint_type == ConstraintType.CARDINALITY

    def involves_role(self, role_id: str) -> bool:
        """Check if a role is part of this constraint's role set."""
        return any(r.id == role_id for r in self.roles)

    def get_role_ids(self) -> List[str]:
        """Get all role IDs in this constraint's role set."""
        return [r.id for r in self.roles]

    def get_conflicting_role_ids(self, role_id: str) -> List[str]:
        """
        For SoD constraints, get all other roles in the set that conflict
        with the given role.

        Args:
            role_id: The role to check

        Returns:
            List of conflicting role IDs, or empty list if not a SoD constraint
            or the role is not part of this constraint
        """
        if not self.is_sod_constraint():
            return []

        if not self.involves_role(role_id):
            return []

        return [r.id for r in self.roles if r.id != role_id]

    def would_violate_sod(self, assigned_role_ids: List[str]) -> bool:
        """
        Check if a set of assigned roles would violate this SoD constraint.

        Per NIST: SSD(role_set, n) is violated when a user holds n or more
        roles from role_set.

        Args:
            assigned_role_ids: The role IDs currently assigned to a user

        Returns:
            True if the assignment violates this constraint
        """
        if not self.is_sod_constraint():
            return False

        constraint_role_ids = set(self.get_role_ids())
        overlap = constraint_role_ids.intersection(set(assigned_role_ids))
        return len(overlap) >= self.threshold

    def would_violate_cardinality(self, current_user_count: int) -> bool:
        """
        Check if adding another user would violate this cardinality constraint.

        Args:
            current_user_count: Number of users currently holding the role

        Returns:
            True if the count meets or exceeds the threshold
        """
        if not self.is_cardinality_constraint():
            return False

        return current_user_count >= self.threshold
