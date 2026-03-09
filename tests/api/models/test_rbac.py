"""Tests for the RBAC models."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.rbac import (
    RBACConstraint,
    RBACPermission,
    RBACRole,
    RBACRolePermission,
    RBACUserRole,
)
from fides.api.models.rbac.rbac_constraint import ConstraintType


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
            db.query(RBACPermission).filter(RBACPermission.code == "test:read").first()
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
        # Create separate roles for each temporal test case to avoid unique constraint violation
        # (only one global assignment per user_id/role_id is allowed)
        future_role_def = RBACRole.create(
            db=db,
            data={
                "name": "Future Temporal Role",
                "key": "future_temporal_role",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        expired_role_def = RBACRole.create(
            db=db,
            data={
                "name": "Expired Temporal Role",
                "key": "expired_temporal_role",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        now = datetime.now(timezone.utc)

        # Create future role assignment (not yet valid)
        future_assignment = RBACUserRole.create(
            db=db,
            data={
                "user_id": user.id,
                "role_id": future_role_def.id,
                "valid_from": now + timedelta(days=1),
            },
            check_name=False,
        )
        db.commit()

        assert future_assignment.is_valid() is False

        # Create expired role assignment
        expired_assignment = RBACUserRole.create(
            db=db,
            data={
                "user_id": user.id,
                "role_id": expired_role_def.id,
                "valid_until": now - timedelta(days=1),
            },
            check_name=False,
        )
        db.commit()

        assert expired_assignment.is_valid() is False


class TestRBACConstraint:
    """Tests for the RBACConstraint model (NIST RBAC standard)."""

    def test_create_pairwise_static_sod(self, db: Session):
        """Test SSD(role_set, 2) — mutual exclusion between two roles."""
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

        # Create SSD({role1, role2}, 2) — user cannot hold both
        constraint = RBACConstraint.create(
            db=db,
            data={
                "name": "Test SOD Constraint",
                "constraint_type": ConstraintType.STATIC_SOD,
                "threshold": 2,
                "is_active": True,
            },
            check_name=False,
        )
        constraint.roles.append(role1)
        constraint.roles.append(role2)
        db.commit()

        assert constraint.name == "Test SOD Constraint"
        assert constraint.constraint_type == ConstraintType.STATIC_SOD
        assert constraint.threshold == 2
        assert constraint.is_sod_constraint() is True
        assert constraint.is_cardinality_constraint() is False
        assert len(constraint.roles) == 2
        assert constraint.involves_role(role1.id) is True
        assert constraint.involves_role(role2.id) is True
        assert constraint.involves_role("nonexistent_id") is False

    def test_multi_role_static_sod(self, db: Session):
        """Test SSD({A, B, C}, 2) — user can hold at most 1 of 3 roles."""
        roles = []
        for i in range(3):
            role = RBACRole.create(
                db=db,
                data={
                    "name": f"Multi SOD Role {i}",
                    "key": f"multi_sod_role_{i}",
                    "is_system_role": False,
                    "is_active": True,
                },
                check_name=False,
            )
            roles.append(role)
        db.commit()

        # Create SSD({A, B, C}, 2) — user can hold at most 1
        constraint = RBACConstraint.create(
            db=db,
            data={
                "name": "Three-way SOD",
                "constraint_type": ConstraintType.STATIC_SOD,
                "threshold": 2,
                "is_active": True,
            },
            check_name=False,
        )
        for role in roles:
            constraint.roles.append(role)
        db.commit()

        assert len(constraint.roles) == 3
        assert constraint.threshold == 2

        # Holding 1 role is fine
        assert constraint.would_violate_sod([roles[0].id]) is False

        # Holding 2 roles violates the constraint
        assert constraint.would_violate_sod([roles[0].id, roles[1].id]) is True

        # Holding all 3 also violates
        assert constraint.would_violate_sod([r.id for r in roles]) is True

        # Holding unrelated roles is fine
        assert constraint.would_violate_sod(["unrelated_role_id"]) is False

    def test_get_conflicting_role_ids(self, db: Session):
        """Test retrieving conflicting roles from a SoD constraint."""
        role1 = RBACRole.create(
            db=db,
            data={
                "name": "Conflict Role A",
                "key": "conflict_role_a",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        role2 = RBACRole.create(
            db=db,
            data={
                "name": "Conflict Role B",
                "key": "conflict_role_b",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        constraint = RBACConstraint.create(
            db=db,
            data={
                "name": "Conflict Constraint",
                "constraint_type": ConstraintType.STATIC_SOD,
                "threshold": 2,
                "is_active": True,
            },
            check_name=False,
        )
        constraint.roles.append(role1)
        constraint.roles.append(role2)
        db.commit()

        # role1's conflicting roles should be [role2]
        conflicting = constraint.get_conflicting_role_ids(role1.id)
        assert conflicting == [role2.id]

        # role2's conflicting roles should be [role1]
        conflicting = constraint.get_conflicting_role_ids(role2.id)
        assert conflicting == [role1.id]

        # Unrelated role returns empty list
        assert constraint.get_conflicting_role_ids("unrelated") == []

    def test_create_dynamic_sod(self, db: Session):
        """Test DSD(role_set, 2) — session-level mutual exclusion."""
        role1 = RBACRole.create(
            db=db,
            data={
                "name": "DSD Role 1",
                "key": "dsd_role_1",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        role2 = RBACRole.create(
            db=db,
            data={
                "name": "DSD Role 2",
                "key": "dsd_role_2",
                "is_system_role": False,
                "is_active": True,
            },
            check_name=False,
        )
        db.commit()

        constraint = RBACConstraint.create(
            db=db,
            data={
                "name": "Dynamic SOD Constraint",
                "constraint_type": ConstraintType.DYNAMIC_SOD,
                "threshold": 2,
                "is_active": True,
            },
            check_name=False,
        )
        constraint.roles.append(role1)
        constraint.roles.append(role2)
        db.commit()

        assert constraint.constraint_type == ConstraintType.DYNAMIC_SOD
        assert constraint.is_sod_constraint() is True

    def test_create_cardinality_constraint(self, db: Session):
        """Test cardinality constraint — max users per role."""
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

        # Cardinality({owner}, 3) — at most 3 users
        constraint = RBACConstraint.create(
            db=db,
            data={
                "name": "Max 3 Users",
                "constraint_type": ConstraintType.CARDINALITY,
                "threshold": 3,
                "is_active": True,
            },
            check_name=False,
        )
        constraint.roles.append(role)
        db.commit()

        assert constraint.constraint_type == ConstraintType.CARDINALITY
        assert constraint.threshold == 3
        assert constraint.is_cardinality_constraint() is True
        assert constraint.is_sod_constraint() is False
        assert len(constraint.roles) == 1

        # 2 users assigned — not violated
        assert constraint.would_violate_cardinality(2) is False

        # 3 users assigned — violated (at threshold)
        assert constraint.would_violate_cardinality(3) is True

        # 4 users assigned — violated
        assert constraint.would_violate_cardinality(4) is True


class TestRBACScopeRegistrySync:
    """Tests to ensure SCOPE_REGISTRY scopes exist in the RBAC migration.

    This prevents drift where scopes are added to SCOPE_REGISTRY but not to
    the RBAC migration. Such drift would cause legacy scopes to not be
    available in the database-driven RBAC system.

    Note: The reverse (RBAC-only scopes that don't exist in SCOPE_REGISTRY)
    is intentionally allowed - new scopes can be added directly to RBAC
    without needing to exist in the legacy system.
    """

    def test_all_scopes_in_registry_have_rbac_migration(self):
        """Every scope in SCOPE_REGISTRY must exist in the RBAC seed migration.

        This test parses the migration file to extract hardcoded SCOPE_DOCS keys
        and verifies all SCOPE_REGISTRY scopes are present.
        """
        import ast
        from pathlib import Path

        from fides.common.api.scope_registry import SCOPE_REGISTRY

        # Find the seed migration file
        migrations_dir = (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "fides"
            / "api"
            / "alembic"
            / "migrations"
            / "versions"
        )
        seed_migration = None
        for f in migrations_dir.glob("*seed_rbac_defaults*.py"):
            seed_migration = f
            break

        assert seed_migration is not None, "Could not find RBAC seed migration file"

        # Parse the migration file to extract SCOPE_DOCS keys
        migration_content = seed_migration.read_text()

        # Find the SCOPE_DOCS dictionary in the migration
        tree = ast.parse(migration_content)
        migration_scopes = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "SCOPE_DOCS":
                        if isinstance(node.value, ast.Dict):
                            for key in node.value.keys:
                                if isinstance(key, ast.Constant):
                                    migration_scopes.add(key.value)

        assert len(migration_scopes) > 0, "Could not parse SCOPE_DOCS from migration"

        registry_scopes = set(SCOPE_REGISTRY)

        # Check for scopes in registry but not in migration
        missing_from_migration = registry_scopes - migration_scopes
        assert not missing_from_migration, (
            f"The following scopes exist in SCOPE_REGISTRY but are missing from the "
            f"RBAC seed migration (seed_rbac_defaults.py). Add them to SCOPE_DOCS in "
            f"the migration:\n{sorted(missing_from_migration)}"
        )
