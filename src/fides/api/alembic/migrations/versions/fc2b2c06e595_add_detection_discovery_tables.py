"""add detection discovery tables

Revision ID: fc2b2c06e595
Revises: c85a641cc92c
Create Date: 2024-04-25 19:53:59.562332

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "fc2b2c06e595"
down_revision = "c85a641cc92c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "stagedresource",
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
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("urn", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("monitor_config_id", sa.String(), nullable=True),
        sa.Column("source_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "classifications",
            sa.ARRAY(postgresql.JSONB(astext_type=sa.Text())),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "user_assigned_data_categories",
            sa.ARRAY(sa.String()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "children", sa.ARRAY(sa.String()), server_default="{}", nullable=False
        ),
        sa.Column("parent", sa.String(), nullable=True),
        sa.Column("diff_status", sa.String(), nullable=True),
        sa.Column(
            "child_diff_statuses",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "meta",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_stagedresource_id"), "stagedresource", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_stagedresource_urn"), "stagedresource", ["urn"], unique=True
    )
    op.create_index(
        op.f("ix_stagedresource_resource_type"),
        "stagedresource",
        ["resource_type"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_stagedresource_resource_type"), table_name="stagedresource")
    op.drop_index(op.f("ix_stagedresource_key"), table_name="stagedresource")
    op.drop_index(op.f("ix_stagedresource_id"), table_name="stagedresource")
    op.drop_table("stagedresource")
    # ### end Alembic commands ###
