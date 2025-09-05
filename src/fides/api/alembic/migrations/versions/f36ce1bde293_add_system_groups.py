"""add system groups

Revision ID: f36ce1bde293
Revises: 78dbe23d8204
Create Date: 2025-08-18 21:36:19.279969

"""

import sqlalchemy as sa
from alembic import op
from citext import CIText

# revision identifiers, used by Alembic.
revision = "f36ce1bde293"
down_revision = "78dbe23d8204"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_group",
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
        sa.Column("fides_key", sa.String(), nullable=False),
        sa.Column(
            "label_color",
            sa.Enum(
                "taxonomy_white",
                "taxonomy_red",
                "taxonomy_orange",
                "taxonomy_yellow",
                "taxonomy_green",
                "taxonomy_blue",
                "taxonomy_purple",
                "sandstone",
                "minos",
                name="customtaxonomycolor",
            ),
            nullable=True,
        ),
        sa.Column("data_steward_username", CIText(), nullable=True),
        sa.Column(
            "data_uses", sa.ARRAY(sa.String()), server_default="{}", nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["data_steward_username"], ["fidesuser.username"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["fides_key"], ["taxonomy_element.fides_key"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_system_group_data_steward_username"),
        "system_group",
        ["data_steward_username"],
        unique=False,
    )
    op.create_index(
        op.f("ix_system_group_fides_key"), "system_group", ["fides_key"], unique=True
    )
    op.create_index(op.f("ix_system_group_id"), "system_group", ["id"], unique=False)
    op.create_table(
        "system_group_member",
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
        sa.Column("system_group_id", sa.String(length=255), nullable=True),
        sa.Column("system_id", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["system_group_id"], ["system_group.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["system_id"], ["ctl_systems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "system_group_id", "system_id", name="uq_system_group_member_group_system"
        ),
    )
    op.create_index(
        op.f("ix_system_group_member_id"), "system_group_member", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_system_group_member_system_group_id"),
        "system_group_member",
        ["system_group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_system_group_member_system_id"),
        "system_group_member",
        ["system_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_system_group_member_system_id"), table_name="system_group_member"
    )
    op.drop_index(
        op.f("ix_system_group_member_system_group_id"), table_name="system_group_member"
    )
    op.drop_index(op.f("ix_system_group_member_id"), table_name="system_group_member")
    op.drop_table("system_group_member")
    op.drop_index(op.f("ix_system_group_id"), table_name="system_group")
    op.drop_index(op.f("ix_system_group_fides_key"), table_name="system_group")
    op.drop_index(
        op.f("ix_system_group_data_steward_username"), table_name="system_group"
    )
    op.drop_table("system_group")
