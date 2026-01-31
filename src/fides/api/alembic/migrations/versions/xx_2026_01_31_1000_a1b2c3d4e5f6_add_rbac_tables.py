"""Add RBAC tables for dynamic role-based access control

Revision ID: a1b2c3d4e5f6
Revises: 627c230d9917
Create Date: 2026-01-31 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "627c230d9917"
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
            comment="Machine-readable key for the role",
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
            comment="Parent role ID for hierarchy",
        ),
        sa.Column(
            "priority",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="Priority for conflict resolution",
        ),
        sa.ForeignKeyConstraint(
            ["parent_role_id"],
            ["rbac_role.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_rbac_role_name"),
        sa.UniqueConstraint("key", name="uq_rbac_role_key"),
    )
    op.create_index(op.f("ix_rbac_role_id"), "rbac_role", ["id"], unique=False)
    op.create_index(op.f("ix_rbac_role_key"), "rbac_role", ["key"], unique=False)
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
            comment="Unique permission code",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Human-readable description",
        ),
        sa.Column(
            "resource_type",
            sa.String(length=100),
            nullable=True,
            comment="Resource type this permission applies to",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
            comment="Whether this permission is active",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_rbac_permission_code"),
    )
    op.create_index(op.f("ix_rbac_permission_id"), "rbac_permission", ["id"], unique=False)
    op.create_index(
        op.f("ix_rbac_permission_code"), "rbac_permission", ["code"], unique=False
    )
    op.create_index(
        op.f("ix_rbac_permission_resource_type"),
        "rbac_permission",
        ["resource_type"],
        unique=False,
    )

    # Create rbac_role_permission junction table
    op.create_table(
        "rbac_role_permission",
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
        sa.Column("role_id", sa.String(length=255), nullable=False),
        sa.Column("permission_id", sa.String(length=255), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "role_id", "permission_id", name="uq_rbac_role_permission_mapping"
        ),
    )
    op.create_index(
        op.f("ix_rbac_role_permission_id"), "rbac_role_permission", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_rbac_role_permission_role_id"),
        "rbac_role_permission",
        ["role_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rbac_role_permission_permission_id"),
        "rbac_role_permission",
        ["permission_id"],
        unique=False,
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
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.String(length=255), nullable=False),
        sa.Column(
            "resource_type",
            sa.String(length=100),
            nullable=True,
            comment="Resource type for scoped permissions",
        ),
        sa.Column(
            "resource_id",
            sa.String(length=255),
            nullable=True,
            comment="Specific resource ID for scoped permissions",
        ),
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            comment="When this assignment becomes active",
        ),
        sa.Column(
            "valid_until",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When this assignment expires",
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
    op.create_index(
        op.f("ix_rbac_user_role_resource"),
        "rbac_user_role",
        ["resource_type", "resource_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rbac_user_role_validity"),
        "rbac_user_role",
        ["valid_from", "valid_until"],
        unique=False,
    )

    # Create rbac_role_constraint table
    op.create_table(
        "rbac_role_constraint",
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
            comment="Type of constraint: static_sod, dynamic_sod, or cardinality",
        ),
        sa.Column(
            "role_id_1",
            sa.String(length=255),
            nullable=False,
            comment="First role in the constraint",
        ),
        sa.Column(
            "role_id_2",
            sa.String(length=255),
            nullable=True,
            comment="Second role (for SoD constraints)",
        ),
        sa.Column(
            "max_users",
            sa.Integer(),
            nullable=True,
            comment="Maximum users for cardinality constraint",
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
            comment="Whether this constraint is enforced",
        ),
        sa.ForeignKeyConstraint(
            ["role_id_1"],
            ["rbac_role.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id_2"],
            ["rbac_role.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rbac_role_constraint_id"),
        "rbac_role_constraint",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rbac_role_constraint_type"),
        "rbac_role_constraint",
        ["constraint_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rbac_role_constraint_role_id_1"),
        "rbac_role_constraint",
        ["role_id_1"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rbac_role_constraint_role_id_2"),
        "rbac_role_constraint",
        ["role_id_2"],
        unique=False,
    )


def downgrade():
    # Drop tables in reverse order of creation
    op.drop_index(
        op.f("ix_rbac_role_constraint_role_id_2"), table_name="rbac_role_constraint"
    )
    op.drop_index(
        op.f("ix_rbac_role_constraint_role_id_1"), table_name="rbac_role_constraint"
    )
    op.drop_index(
        op.f("ix_rbac_role_constraint_type"), table_name="rbac_role_constraint"
    )
    op.drop_index(op.f("ix_rbac_role_constraint_id"), table_name="rbac_role_constraint")
    op.drop_table("rbac_role_constraint")

    op.drop_index(op.f("ix_rbac_user_role_validity"), table_name="rbac_user_role")
    op.drop_index(op.f("ix_rbac_user_role_resource"), table_name="rbac_user_role")
    op.drop_index(op.f("ix_rbac_user_role_role_id"), table_name="rbac_user_role")
    op.drop_index(op.f("ix_rbac_user_role_user_id"), table_name="rbac_user_role")
    op.drop_index(op.f("ix_rbac_user_role_id"), table_name="rbac_user_role")
    op.drop_table("rbac_user_role")

    op.drop_index(
        op.f("ix_rbac_role_permission_permission_id"), table_name="rbac_role_permission"
    )
    op.drop_index(
        op.f("ix_rbac_role_permission_role_id"), table_name="rbac_role_permission"
    )
    op.drop_index(op.f("ix_rbac_role_permission_id"), table_name="rbac_role_permission")
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
