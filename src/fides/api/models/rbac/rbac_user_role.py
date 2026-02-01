"""RBAC User-Role assignment model with resource scoping and temporal validity."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base

if TYPE_CHECKING:
    from fides.api.models.fides_user import FidesUser
    from fides.api.models.rbac.rbac_role import RBACRole


class RBACUserRole(Base):
    """
    User to role assignment with optional resource scoping and temporal validity.

    This table supports:
    - Global role assignments: resource_type and resource_id are NULL
    - Resource-scoped assignments: permissions apply only to specific resources
    - Temporal roles: valid_from/valid_until define when the assignment is active

    Examples:
    - Global admin: role=owner, resource_type=NULL, resource_id=NULL
    - System manager: role=system_manager, resource_type='system', resource_id='sys_123'
    - Temporary access: valid_from=now, valid_until=now+30days
    """

    __tablename__ = "rbac_user_role"

    user_id = Column(
        String(255),
        ForeignKey("fidesuser.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to fidesuser",
    )
    role_id = Column(
        String(255),
        ForeignKey("rbac_role.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to rbac_role",
    )
    resource_type = Column(
        String(100),
        nullable=True,
        comment="Resource type for scoped permissions, e.g., 'system'. NULL for global.",
    )
    resource_id = Column(
        String(255),
        nullable=True,
        comment="Specific resource ID for scoped permissions. NULL for global.",
    )
    valid_from = Column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=True,
        comment="When this assignment becomes active. NULL means immediately.",
    )
    valid_until = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this assignment expires. NULL means never expires.",
    )
    assigned_by = Column(
        String(255),
        ForeignKey("fidesuser.id", ondelete="SET NULL"),
        nullable=True,
        comment="User ID of who created this assignment",
    )

    # Relationships
    user: "FidesUser" = relationship(
        "FidesUser",
        foreign_keys=[user_id],
        backref="rbac_role_assignments",
        passive_deletes=True,  # Let database handle CASCADE delete
    )
    role: "RBACRole" = relationship(
        "RBACRole",
        back_populates="user_assignments",
        lazy="selectin",
    )
    assigner: Optional["FidesUser"] = relationship(
        "FidesUser",
        foreign_keys=[assigned_by],
    )

    # Ensure unique combination of user, role, resource_type, resource_id
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            "resource_type",
            "resource_id",
            name="uq_rbac_user_role_assignment",
        ),
    )

    def __repr__(self) -> str:
        scope = f"{self.resource_type}:{self.resource_id}" if self.resource_type else "global"
        return f"<RBACUserRole(user_id='{self.user_id}', role_id='{self.role_id}', scope='{scope}')>"

    def is_valid(self) -> bool:
        """
        Check if this role assignment is currently valid based on temporal constraints.

        Returns:
            True if the assignment is currently active, False otherwise
        """
        now = datetime.now(timezone.utc)

        # Check valid_from
        if self.valid_from:
            # Ensure comparison is timezone-aware
            valid_from = self.valid_from
            if valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=timezone.utc)
            if valid_from > now:
                return False

        # Check valid_until
        if self.valid_until:
            # Ensure comparison is timezone-aware
            valid_until = self.valid_until
            if valid_until.tzinfo is None:
                valid_until = valid_until.replace(tzinfo=timezone.utc)
            if valid_until < now:
                return False

        return True

    def is_global(self) -> bool:
        """Check if this is a global (non-resource-scoped) assignment."""
        return self.resource_type is None and self.resource_id is None

    def matches_resource(
        self, resource_type: Optional[str], resource_id: Optional[str]
    ) -> bool:
        """
        Check if this assignment applies to a specific resource.

        Args:
            resource_type: The type of resource being accessed
            resource_id: The specific resource ID being accessed

        Returns:
            True if this assignment grants access to the resource
        """
        # Global assignments match everything
        if self.is_global():
            return True

        # Resource type must match
        if self.resource_type != resource_type:
            return False

        # If assignment has specific resource_id, it must match
        if self.resource_id is not None:
            return self.resource_id == resource_id

        # Assignment applies to all resources of this type
        return True
