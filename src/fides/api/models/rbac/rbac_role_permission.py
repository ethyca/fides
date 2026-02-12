"""RBAC Role-Permission junction table.

Implements Permission-Role Assignment (PA) from the NIST RBAC standard
(ANSI/INCITS 359-2004). Each row maps a permission directly to a role.

See: https://csrc.nist.gov/projects/role-based-access-control
"""

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func

from fides.api.db.base_class import Base


class RBACRolePermission(Base):
    """
    Junction table for role-permission assignments.

    This is a many-to-many mapping between roles and permissions.
    Each row represents a permission that is directly assigned to a role.

    Note: This table does not track inherited permissions. Inheritance is
    computed at runtime via the role hierarchy.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "rbac_role_permission"

    # Override Base.id - junction table uses composite PK instead
    id = None  # type: ignore[assignment]
    # Override Base.updated_at - junction table doesn't need this
    updated_at = None  # type: ignore[assignment]

    # Composite primary key: (role_id, permission_id)
    role_id = Column(
        String(255),
        ForeignKey("rbac_role.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK to rbac_role",
    )
    permission_id = Column(
        String(255),
        ForeignKey("rbac_permission.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK to rbac_permission",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="When this permission was assigned to the role",
    )

    def __repr__(self) -> str:
        return f"<RBACRolePermission(role_id='{self.role_id}', permission_id='{self.permission_id}')>"
