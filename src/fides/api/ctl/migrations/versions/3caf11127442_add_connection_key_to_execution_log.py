"""Add connection key to execution log

Revision ID: 3caf11127442
Revises: 1f61c765cd1c
Create Date: 2022-12-21 13:36:17.859959

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3caf11127442"
down_revision = "1f61c765cd1c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "executionlog", sa.Column("connection_key", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_executionlog_connection_key"),
        "executionlog",
        ["connection_key"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_executionlog_connection_key"), table_name="executionlog")
    op.drop_column("executionlog", "connection_key")
    # ### end Alembic commands ###
