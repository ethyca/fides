"""create custom_connector_template

Revision ID: 8615ac51e78b
Revises: 39a23bc016ea
Create Date: 2023-03-20 15:11:52.634508

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8615ac51e78b"
down_revision = "39a23bc016ea"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "custom_connector_template",
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
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("config", sa.String(), nullable=False),
        sa.Column("dataset", sa.String(), nullable=False),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("functions", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_custom_connector_template_id"),
        "custom_connector_template",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_custom_connector_template_key"),
        "custom_connector_template",
        ["key"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        op.f("ix_custom_connector_template_key"), table_name="custom_connector_template"
    )
    op.drop_index(
        op.f("ix_custom_connector_template_id"), table_name="custom_connector_template"
    )
    op.drop_table("custom_connector_template")
