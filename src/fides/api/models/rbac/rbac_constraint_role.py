"""RBAC Constraint-Role junction table.

Links roles to constraints, forming the role_set in NIST RBAC constraint
definitions: SSD(role_set, n) and DSD(role_set, n).

See: https://csrc.nist.gov/projects/role-based-access-control
"""

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func

from fides.api.db.base_class import Base


class RBACConstraintRole(Base):
    """
    Junction table linking roles to constraints.

    Each row represents a role that is part of a constraint's role_set.
    A constraint can have any number of roles, enabling multi-role SoD
    constraints (not just pairwise).

    Per NIST RBAC: the role_set in SSD(role_set, n) and DSD(role_set, n)
    is represented by all rows sharing the same constraint_id.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "rbac_constraint_role"

    # Override Base.id — junction table uses composite PK instead
    id = None  # type: ignore[assignment]
    # Override Base.updated_at — junction table doesn't need this
    updated_at = None  # type: ignore[assignment]

    # Composite primary key: (constraint_id, role_id)
    constraint_id = Column(
        String(255),
        ForeignKey("rbac_constraint.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK to rbac_constraint",
    )
    role_id = Column(
        String(255),
        ForeignKey("rbac_role.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK to rbac_role",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="When this role was added to the constraint set",
    )

    def __repr__(self) -> str:
        return f"<RBACConstraintRole(constraint_id='{self.constraint_id}', role_id='{self.role_id}')>"
