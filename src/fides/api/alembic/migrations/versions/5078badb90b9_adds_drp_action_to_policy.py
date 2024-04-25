"""adds DRP action to policy

Revision ID: 5078badb90b9
Revises: c98da12d76f8
Create Date: 2022-05-04 17:22:46.500067

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy.dialects import postgresql

revision = "5078badb90b9"
down_revision = "c98da12d76f8"
branch_labels = None
depends_on = None


def upgrade():
    drpaction = postgresql.ENUM(
        "access",
        "deletion",
        "sale_opt_out",
        "sale_opt_in",
        "access_categories",
        "access_specific",
        name="drpaction",
        create_type=False,
    )
    drpaction.create(op.get_bind())
    op.add_column("policy", sa.Column("drp_action", drpaction, nullable=True))
    op.create_index(op.f("ix_policy_drp_action"), "policy", ["drp_action"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_policy_drp_action"), table_name="policy")
    op.drop_column("policy", "drp_action")
    op.execute("DROP TYPE drpaction;")
