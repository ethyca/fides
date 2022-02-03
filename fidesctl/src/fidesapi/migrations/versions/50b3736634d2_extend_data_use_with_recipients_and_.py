"""extend data_use with recipients and legal_basis

Revision ID: 50b3736634d2
Revises: 1739aa4a4ab7
Create Date: 2022-02-03 18:03:16.120608

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "50b3736634d2"
down_revision = "1739aa4a4ab7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("data_uses", sa.Column("legal_basis", sa.Text(), nullable=True))
    op.add_column(
        "data_uses",
        sa.Column("recipients", postgresql.ARRAY(sa.VARCHAR()), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("data_uses", "recipients")
    op.drop_column("data_uses", "legal_basis")
    # ### end Alembic commands ###
