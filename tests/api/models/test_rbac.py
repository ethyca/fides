"""Tests for the RBAC models."""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.rbac import (
    RBACPermission,
    RBACRole,
    RBACRoleConstraint,
    RBACRolePermission,
    RBACUserRole,
)
from fides.api.models.rbac.rbac_role_constraint import ConstraintType


class TestRBACPermission:
    """Tests for the RBACPermission model."""

    def test_create_permission(self, db: Session):
        """Test creating an RBACPermission record."""
        permission = RBACPermission.create(
            db=db,
            data={
                "code": "test:read",
                "description": "Test read permission",
                "resource_type": "test",
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        assert permission.code == "test:read"
        assert permission.description == "Test read permission"
        assert permission.resource_type == "test"
        assert permission.is_active is True

        # Verify persistence
        retrieved = (
            db.query(RBACPermission)
            .filter(RBACPermission.code == "test:read")
            .first()
        )
        assert retrieved is not None
        assert retrieved.code == "test:read"


class TestRBACRole:
    """Tests for the RBACRole model."""

    def test_create_custom_role(self, db: Session):
        """Test creating a custom RBAC role."""
        role = RBACRole.create(
            db=db,
            data={
                "name": "Test Role",
                "key": "test_role",
                "description": "A test role for unit testing",
                "priority": 10,
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        assert role.name == "Test Role"
        assert role.key == "test_role"
        assert role.description == "A test role for unit testing"
        assert role.priority == 10
        assert role.is_system_role is False
        assert role.is_active is True

    def test_create_role_with_parent(self, db: Session):
        """Test creating a role with parent role hierarchy."""
        # Create parent role
        parent_role = RBACRole.create(
            db=db,
            data={
                "name": "Parent Role",
                "key": "parent_role",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        # Create child role
        child_role = RBACRole.create(
            db=db,
            data={
                "name": "Child Role",
                "key": "child_role",
                "parent_role_id": parent_role.id,
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        assert child_role.parent_role_id == parent_role.id
        assert child_role.parent_role.id == parent_role.id
        assert parent_role.child_roles[0].id == child_role.id

    def test_role_permission_inheritance(self, db: Session):
        """Test that child roles inherit permissions from parent roles."""
        # Create permission
        permission = RBACPermission.create(
            db=db,
            data={
                "code": "inherited:permission",
                "description": "Permission to be inherited",
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        # Create parent role with permission
        parent_role = RBACRole.create(
            db=db,
            data={
                "name": "Inheriting Parent",
                "key": "inheriting_parent",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        parent_role.permissions.append(permission)
        db.commit()

        # Create child role
        child_role = RBACRole.create(
            db=db,
            data={
                "name": "Inheriting Child",
                "key": "inheriting_child",
                "parent_role_id": parent_role.id,
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        # Test inheritance
        all_permissions = child_role.get_all_permissions(db)
        assert any(p.code == "inherited:permission" for p in all_permissions)

        # Test inherited permission codes
        inherited_codes = child_role.get_inherited_permission_codes(db)
        assert "inherited:permission" in inherited_codes


class TestRBACUserRole:
    """Tests for the RBACUserRole model."""

    def test_assign_role_to_user(self, db: Session, user: FidesUser):
        """Test assigning a role to a user."""
        # Create role
        role = RBACRole.create(
            db=db,
            data={
                "name": "User Test Role",
                "key": "user_test_role",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        # Assign role to user
        user_role = RBACUserRole.create(
            db=db,
            data={
                "user_id": user.id,
                "role_id": role.id,
                "assigned_by": user.id,
            },
            check_name=False,
        )
        db.commit()

        assert user_role.user_id == user.id
        assert user_role.role_id == role.id
        assert user_role.role.key == "user_test_role"
        assert user_role.is_valid() is True

    def test_scoped_role_assignment(self, db: Session, user: FidesUser):
        """Test assigning a role with resource scoping."""
        role = RBACRole.create(
            db=db,
            data={
                "name": "Scoped Role",
                "key": "scoped_role",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        # Assign scoped role
        user_role = RBACUserRole.create(
            db=db,
            data={
                "user_id": user.id,
                "role_id": role.id,
                "resource_type": "system",
                "resource_id": "system_123",
            },
            check_name=False,
        )
        db.commit()

        assert user_role.resource_type == "system"
        assert user_role.resource_id == "system_123"
        assert user_role.is_global() is False
        assert user_role.matches_resource("system", "system_123") is True
        assert user_role.matches_resource("system", "system_456") is False
        assert user_role.matches_resource("other", "system_123") is False

    def test_temporal_role_assignment(self, db: Session, user: FidesUser):
        """Test temporal validity of role assignments."""
        role = RBACRole.create(
            db=db,
            data={
                "name": "Temporal Role",
                "key": "temporal_role",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        now = datetime.now(timezone.utc)

        # Create future role (not yet valid)
        future_role = RBACUserRole.create(
            db=db,
            data={
                "user_id": user.id,
                "role_id": role.id,
                "valid_from": now + timedelta(days=1),
            },
            check_name=False,
        )
        db.commit()

        assert future_role.is_valid() is False

        # Create expired role
        expired_role = RBACUserRole.create(
            db=db,
            data={
                "user_id": user.id,
                "role_id": role.id,
                "valid_until": now - timedelta(days=1),
            },
            check_name=False,
        )
        db.commit()

        assert expired_role.is_valid() is False


class TestRBACRoleConstraint:
    """Tests for the RBACRoleConstraint model."""

    def test_create_sod_constraint(self, db: Session):
        """Test creating a separation of duties constraint."""
        # Create two roles
        role1 = RBACRole.create(
            db=db,
            data={
                "name": "SOD Role 1",
                "key": "sod_role_1",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        role2 = RBACRole.create(
            db=db,
            data={
                "name": "SOD Role 2",
                "key": "sod_role_2",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        # Create SOD constraint
        constraint = RBACRoleConstraint.create(
            db=db,
            data={
                "name": "Test SOD Constraint",
                "constraint_type": ConstraintType.STATIC_SOD,
                "role_id_1": role1.id,
                "role_id_2": role2.id,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        assert constraint.name == "Test SOD Constraint"
        assert constraint.constraint_type == ConstraintType.STATIC_SOD
        assert constraint.role_id_1 == role1.id
        assert constraint.role_id_2 == role2.id

    def test_create_cardinality_constraint(self, db: Session):
        """Test creating a cardinality constraint."""
        role = RBACRole.create(
            db=db,
            data={
                "name": "Cardinality Role",
                "key": "cardinality_role",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        # Create cardinality constraint
        constraint = RBACRoleConstraint.create(
            db=db,
            data={
                "name": "Max 5 Users",
                "constraint_type": ConstraintType.CARDINALITY,
                "role_id_1": role.id,
                "max_users": 5,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        assert constraint.constraint_type == ConstraintType.CARDINALITY
        assert constraint.max_users == 5
