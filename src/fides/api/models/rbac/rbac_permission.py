"""RBAC Permission model for storing permission definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base

if TYPE_CHECKING:
    from fides.api.models.rbac.rbac_role import RBACRole


class RBACPermission(Base):
    """
    Permission definition for RBAC system.

    Permissions are the atomic units of access control. Each permission represents
    a specific action that can be performed on a resource type.

    Permissions are seeded from the existing SCOPE_REGISTRY and should not be
    created manually in most cases.
    """

    __tablename__ = "rbac_permission"

    code = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique permission code, e.g., 'system:read', 'privacy-request:create'",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description of what this permission allows",
    )
    resource_type = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Resource type this permission applies to, e.g., 'system', 'privacy_request'. NULL for global permissions.",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Whether this permission is currently active and can be assigned",
    )

    # Relationships
    roles: List["RBACRole"] = relationship(
        "RBACRole",
        secondary="rbac_role_permission",
        back_populates="permissions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<RBACPermission(code='{self.code}')>"
