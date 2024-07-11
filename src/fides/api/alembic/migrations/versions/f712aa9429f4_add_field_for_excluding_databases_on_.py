"""add field for excluding databases on MonitorConfig model

Revision ID: f712aa9429f4
Revises: 31493e48c1d8
Create Date: 2024-07-11 18:00:14.221036

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f712aa9429f4"
down_revision = "31493e48c1d8"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        op.f("ix_consentrequest_property_id"),
        "consentrequest",
        ["property_id"],
        unique=False,
    )
    op.add_column(
        "monitorconfig",
        sa.Column(
            "excluded_databases",
            sa.ARRAY(sa.String()),
            server_default="{}",
            nullable=False,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("monitorconfig", "excluded_databases")
    op.drop_index(op.f("ix_consentrequest_property_id"), table_name="consentrequest")
    # ### end Alembic commands ###
