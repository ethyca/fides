"""system_managers

Revision ID: 68a518a3c050
Revises: eb1e6ec39b83
Create Date: 2023-02-23 21:52:56.225405

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "68a518a3c050"
down_revision = "eb1e6ec39b83"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "systemmanager",
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
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("system_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["system_id"],
            ["ctl_systems.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["fidesuser.id"],
        ),
        sa.PrimaryKeyConstraint("id", "user_id", "system_id"),
    )
    op.create_index(op.f("ix_systemmanager_id"), "systemmanager", ["id"], unique=False)
    op.add_column(
        "client",
        sa.Column(
            "systems", sa.ARRAY(sa.String()), server_default="{}", nullable=False
        ),
    )


def downgrade():
    op.drop_column("client", "systems")
    op.drop_index(op.f("ix_systemmanager_id"), table_name="systemmanager")
    op.drop_table("systemmanager")
