"""Add RBAC tables for dynamic role-based access control

Revision ID: d9ee4ea46797
Revises: f85bd4c08401
Create Date: 2026-01-31 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d9ee4ea46797"
down_revision = "f85bd4c08401"
branch_labels = None
depends_on = None


def upgrade():
    # Create rbac_role table
    op.create_table(
        "rbac_role",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
            comment="Human-readable display name for the role",
        ),
        sa.Column(
            "key",
            sa.String(length=255),
            nullable=False,
            comment="Machine-readable key for the role, e.g., 'owner', 'custom_auditor'",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Description of the role's purpose and access level",
        ),
        sa.Column(
            "is_system_role",
            sa.Boolean(),
            server_default="false",
            nullable=False,
            comment="True for built-in system roles that cannot be deleted",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
            comment="Whether this role can be assigned to users",
        ),
        sa.Column(
            "parent_role_id",
            sa.String(length=255),
            nullable=True,
            comment="Parent role ID for hierarchy. Child roles inherit parent permissions.",
        ),
        sa.Column(
            "priority",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="Priority for conflict resolution. Higher values = more privileges.",
        ),
        sa.ForeignKeyConstraint(
            ["parent_role_id"],
            ["rbac_role.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_rbac_role_name"),
    )
    op.create_index(op.f("ix_rbac_role_id"), "rbac_role", ["id"], unique=False)
    op.create_index(op.f("ix_rbac_role_key"), "rbac_role", ["key"], unique=True)
    op.create_index(
        op.f("ix_rbac_role_parent_role_id"), "rbac_role", ["parent_role_id"], unique=False
    )

    # Create rbac_permission table
    op.create_table(
        "rbac_permission",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "code",
            sa.String(length=255),
            nullable=False,
            comment="Unique permission code, e.g., 'system:read', 'privacy-request:create'",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Human-readable description of what this permission allows",
        ),
        sa.Column(
            "resource_type",
            sa.String(length=100),
            nullable=True,
            comment="Resource type this permission applies to, e.g., 'system', 'privacy_request'. NULL for global permissions.",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
            comment="Whether this permission is currently active and can be assigned",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rbac_permission_id"), "rbac_permission", ["id"], unique=False)
    op.create_index(
        op.f("ix_rbac_permission_code"), "rbac_permission", ["code"], unique=True
    )
    op.create_index(
        op.f("ix_rbac_permission_resource_type"),
        "rbac_permission",
        ["resource_type"],
        unique=False,
    )

    # Create rbac_role_permission junction table (composite PK)
    op.create_table(
        "rbac_role_permission",
        sa.Column(
            "role_id",
            sa.String(length=255),
            nullable=False,
            comment="FK to rbac_role",
        ),
        sa.Column(
            "permission_id",
            sa.String(length=255),
            nullable=False,
            comment="FK to rbac_permission",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            comment="When this permission was assigned to the role",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["rbac_role.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["rbac_permission.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    # Create rbac_user_role table
    op.create_table(
        "rbac_user_role",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            sa.String(length=255),
            nullable=False,
            comment="FK to fidesuser",
        ),
        sa.Column(
            "role_id",
            sa.String(length=255),
            nullable=False,
            comment="FK to rbac_role",
        ),
        sa.Column(
            "resource_type",
            sa.String(length=100),
            nullable=True,
            comment="Resource type for scoped permissions, e.g., 'system'. NULL for global.",
        ),
        sa.Column(
            "resource_id",
            sa.String(length=255),
            nullable=True,
            comment="Specific resource ID for scoped permissions. NULL for global.",
        ),
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            comment="When this assignment becomes active. NULL means immediately.",
        ),
        sa.Column(
            "valid_until",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When this assignment expires. NULL means never expires.",
        ),
        sa.Column(
            "assigned_by",
            sa.String(length=255),
            nullable=True,
            comment="User ID of who created this assignment",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["fidesuser.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["rbac_role.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by"],
            ["fidesuser.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "role_id",
            "resource_type",
            "resource_id",
            name="uq_rbac_user_role_assignment",
        ),
    )
    op.create_index(
        op.f("ix_rbac_user_role_id"), "rbac_user_role", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_rbac_user_role_user_id"), "rbac_user_role", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_rbac_user_role_role_id"), "rbac_user_role", ["role_id"], unique=False
    )

    # Create rbac_constraint table
    # Implements NIST RBAC (ANSI/INCITS 359-2004) constraint model:
    # SSD(role_set, n) and DSD(role_set, n) where role_set is linked via
    # rbac_constraint_role junction table and n is the threshold column.
    op.create_table(
        "rbac_constraint",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
            comment="Human-readable name for this constraint",
        ),
        sa.Column(
            "constraint_type",
            sa.String(length=50),
            nullable=False,
            comment="Type of constraint: static_sod, dynamic_sod, or cardinality (per NIST RBAC)",
        ),
        sa.Column(
            "threshold",
            sa.Integer(),
            nullable=False,
            comment=(
                "NIST 'n' value. For SoD: max roles from set a user can hold/activate "
                "(e.g. 2 = mutual exclusion for a 2-role set). "
                "For cardinality: max users that can hold any role in the set."
            ),
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Description of why this constraint exists",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
            comment="Whether this constraint is currently enforced",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rbac_constraint_id"),
        "rbac_constraint",
        ["id"],
        unique=False,
    )

    # Create rbac_constraint_role junction table (composite PK)
    # Links roles to constraints, forming the role_set in NIST SSD/DSD definitions.
    op.create_table(
        "rbac_constraint_role",
        sa.Column(
            "constraint_id",
            sa.String(length=255),
            nullable=False,
            comment="FK to rbac_constraint",
        ),
        sa.Column(
            "role_id",
            sa.String(length=255),
            nullable=False,
            comment="FK to rbac_role",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            comment="When this role was added to the constraint set",
        ),
        sa.ForeignKeyConstraint(
            ["constraint_id"],
            ["rbac_constraint.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["rbac_role.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("constraint_id", "role_id"),
    )


def downgrade():
    # Drop tables in reverse order of creation
    op.drop_table("rbac_constraint_role")
    op.drop_index(op.f("ix_rbac_constraint_id"), table_name="rbac_constraint")
    op.drop_table("rbac_constraint")

    op.drop_index(op.f("ix_rbac_user_role_role_id"), table_name="rbac_user_role")
    op.drop_index(op.f("ix_rbac_user_role_user_id"), table_name="rbac_user_role")
    op.drop_index(op.f("ix_rbac_user_role_id"), table_name="rbac_user_role")
    op.drop_table("rbac_user_role")

    op.drop_table("rbac_role_permission")

    op.drop_index(
        op.f("ix_rbac_permission_resource_type"), table_name="rbac_permission"
    )
    op.drop_index(op.f("ix_rbac_permission_code"), table_name="rbac_permission")
    op.drop_index(op.f("ix_rbac_permission_id"), table_name="rbac_permission")
    op.drop_table("rbac_permission")

    op.drop_index(op.f("ix_rbac_role_parent_role_id"), table_name="rbac_role")
    op.drop_index(op.f("ix_rbac_role_key"), table_name="rbac_role")
    op.drop_index(op.f("ix_rbac_role_id"), table_name="rbac_role")
    op.drop_table("rbac_role")
