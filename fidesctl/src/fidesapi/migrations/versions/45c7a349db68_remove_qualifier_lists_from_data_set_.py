"""Remove qualifier lists from data set models

Revision ID: 45c7a349db68
Revises: 732105cd54e3
Create Date: 2021-10-25 17:59:25.244689

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "45c7a349db68"
down_revision = "732105cd54e3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("datasets", sa.Column("data_qualifier", sa.String(), nullable=True))
    op.drop_column("datasets", "data_qualifiers")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "datasets",
        sa.Column(
            "data_qualifiers",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.drop_column("datasets", "data_qualifier")
    # ### end Alembic commands ###
