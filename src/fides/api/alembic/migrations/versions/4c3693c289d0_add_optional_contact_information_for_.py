"""Add optional contact information for organization, system, and dataset

Revision ID: 4c3693c289d0
Revises: 7c851d8a102a
Create Date: 2022-01-21 15:56:53.519486

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import BYTEA

# revision identifiers, used by Alembic.
revision = "4c3693c289d0"
down_revision = "7c851d8a102a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.add_column("datasets", sa.Column("joint_controller", BYTEA, nullable=True))
    op.drop_column("evaluations", "updated_at")
    op.drop_column("evaluations", "created_at")
    op.add_column("organizations", sa.Column("controller", BYTEA, nullable=True))
    op.add_column(
        "organizations", sa.Column("data_protection_officer", BYTEA, nullable=True)
    )
    op.add_column("organizations", sa.Column("representative", BYTEA, nullable=True))
    op.add_column("systems", sa.Column("joint_controller", BYTEA, nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("systems", "joint_controller")
    op.drop_column("organizations", "controller")
    op.drop_column("organizations", "data_protection_officer")
    op.drop_column("organizations", "representative")
    op.add_column(
        "evaluations",
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "evaluations",
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_column("datasets", "joint_controller")
    # ### end Alembic commands ###