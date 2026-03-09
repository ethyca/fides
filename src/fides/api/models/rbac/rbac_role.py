"""RBAC Role model for dynamic role definitions.

Implements the Roles component of the NIST RBAC standard (ANSI/INCITS 359-2004),
including support for Hierarchical RBAC (General Hierarchy) via parent_role_id.

See: https://csrc.nist.gov/projects/role-based-access-control
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Set, Union

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty, Session, relationship

from fides.api.db.base_class import Base

if TYPE_CHECKING:
    from fides.api.models.rbac.rbac_permission import RBACPermission
    from fides.api.models.rbac.rbac_user_role import RBACUserRole


class RBACRole(Base):
    """
    Dynamic role definition following the NIST RBAC standard (ANSI/INCITS 359-2004).

    Roles group permissions together and can form hierarchies (General Hierarchy)
    where child roles inherit permissions from parent roles. System roles
    (is_system_role=True) are the built-in roles migrated from the legacy
    hardcoded system and cannot be deleted or have their core properties modified.

    Role hierarchy is implemented via parent_role_id. When checking permissions,
    a role's effective permissions include both its directly assigned permissions
    and all permissions inherited from ancestor roles (NIST Hierarchical RBAC).
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Return the database table name for this model."""
        return "rbac_role"

    name = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="Human-readable display name for the role",
    )
    key = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Machine-readable key for the role, e.g., 'owner', 'custom_auditor'",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Description of the role's purpose and access level",
    )
    is_system_role = Column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True for built-in system roles that cannot be deleted",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Whether this role can be assigned to users",
    )
    parent_role_id = Column(
        String(255),
        ForeignKey("rbac_role.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent role ID for hierarchy. Child roles inherit parent permissions.",
    )
    priority = Column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Priority for conflict resolution. Higher values = more privileges.",
    )

    # Self-referential relationship for hierarchy
    parent_role: RelationshipProperty[Optional["RBACRole"]] = relationship(
        "RBACRole",
        remote_side="RBACRole.id",
        backref="child_roles",
        foreign_keys=[parent_role_id],
    )

    # Permissions assigned directly to this role
    permissions: RelationshipProperty[List["RBACPermission"]] = relationship(
        "RBACPermission",
        secondary="rbac_role_permission",
        back_populates="roles",
        lazy="selectin",
    )

    # User assignments for this role
    user_assignments: RelationshipProperty[List["RBACUserRole"]] = relationship(
        "RBACUserRole",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return a string representation of this role."""
        return f"<RBACRole(key='{self.key}', name='{self.name}')>"

    def get_all_permissions(
        self, db: Session, _visited_role_ids: Optional[Set[Union[str, int]]] = None
    ) -> List["RBACPermission"]:
        """
        Get all permissions for this role, including inherited from parent roles.

        This method traverses the role hierarchy and collects all permissions
        from this role and all ancestor roles. Cycle detection prevents infinite
        recursion if a cyclic parent_role_id chain exists. Uses id(self) as
        fallback for transient instances where self.id is None before persistence.

        Args:
            db: Database session (needed for lazy-loaded relationships)
            _visited_role_ids: Internal set for cycle detection (do not pass externally)

        Returns:
            List of unique RBACPermission objects
        """
        # Initialize or copy visited set for cycle detection
        if _visited_role_ids is None:
            _visited_role_ids = set()

        # Use id(self) as fallback for transient instances (self.id is None before persist)
        # This prevents false positives when building hierarchies in-memory
        role_key = self.id if self.id is not None else id(self)

        # Detect cycle: if we've already visited this role, stop traversal
        if role_key in _visited_role_ids:
            return []
        _visited_role_ids.add(role_key)

        seen_permission_ids: Set[str] = set()
        all_permissions: List["RBACPermission"] = []

        # Add direct permissions
        for permission in self.permissions:
            if permission.id not in seen_permission_ids and permission.is_active:
                seen_permission_ids.add(permission.id)
                all_permissions.append(permission)

        # Add inherited permissions from parent hierarchy
        if self.parent_role:
            for permission in self.parent_role.get_all_permissions(
                db, _visited_role_ids
            ):
                if permission.id not in seen_permission_ids and permission.is_active:
                    seen_permission_ids.add(permission.id)
                    all_permissions.append(permission)

        return all_permissions

    def get_permission_codes(self, db: Session) -> List[str]:
        """
        Get all permission codes for this role, including inherited.

        Args:
            db: Database session

        Returns:
            List of unique permission code strings
        """
        return [p.code for p in self.get_all_permissions(db)]

    def get_direct_permission_codes(self) -> List[str]:
        """
        Get only the directly assigned permission codes (not inherited).

        Returns:
            List of permission code strings directly assigned to this role
        """
        return [p.code for p in self.permissions if p.is_active]

    def get_inherited_permission_codes(self, db: Session) -> List[str]:
        """
        Get only the inherited permission codes (from parent roles).

        Args:
            db: Database session

        Returns:
            List of permission codes inherited from parent roles
        """
        direct_codes = set(self.get_direct_permission_codes())
        all_codes = set(self.get_permission_codes(db))
        return list(all_codes - direct_codes)

    def get_ancestor_roles(self) -> List["RBACRole"]:
        """
        Get all ancestor roles in the hierarchy (parent, grandparent, etc.).

        Cycle detection prevents infinite loops if a cyclic parent_role_id
        chain exists in the database. Uses id(self) as fallback for transient
        instances where self.id is None before persistence.

        Returns:
            List of ancestor RBACRole objects, starting with immediate parent
        """
        ancestors: List["RBACRole"] = []
        # Use id(self) fallback for transient instances (self.id is None before persist)
        self_key = self.id if self.id is not None else id(self)
        visited_keys: Set[Union[str, int]] = {
            self_key
        }  # Include self to detect immediate cycle
        current = self.parent_role
        while current:
            # Use id() fallback for transient instances
            current_key = current.id if current.id is not None else id(current)
            # Detect cycle: stop if we've already seen this role
            if current_key in visited_keys:
                break
            visited_keys.add(current_key)
            ancestors.append(current)
            current = current.parent_role
        return ancestors
