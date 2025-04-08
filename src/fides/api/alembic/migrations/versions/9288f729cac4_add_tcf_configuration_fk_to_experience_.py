"""Add tcf_configuration FK to experience config

Revision ID: 9288f729cac4
Revises: 99c603c1b8f9
Create Date: 2025-04-07 18:49:31.843362

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9288f729cac4"
down_revision = "99c603c1b8f9"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("tcf_configuration_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "privacyexperienceconfig_tcf_configuration_fkey",
        "privacyexperienceconfig",
        "tcf_configuration",
        ["tcf_configuration_id"],
        ["id"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "privacyexperienceconfig_tcf_configuration_fkey",
        "privacyexperienceconfig",
        type_="foreignkey",
    )
    op.drop_column("privacyexperienceconfig", "tcf_configuration_id")
    # ### end Alembic commands ###
