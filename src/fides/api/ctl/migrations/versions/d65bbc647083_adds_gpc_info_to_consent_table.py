"""adds GPC info to consent table

Revision ID: d65bbc647083
Revises: c9ee230fa6da
Create Date: 2023-02-15 13:57:36.159161

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d65bbc647083"
down_revision = "c9ee230fa6da"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("consent", sa.Column("has_gpc_flag", sa.Boolean(), nullable=True))
    op.add_column(
        "consent", sa.Column("conflicts_with_gpc", sa.Boolean(), nullable=True)
    )
    op.execute("UPDATE consent SET has_gpc_flag = false")
    op.alter_column(
        "consent", "has_gpc_flag", server_default="f", default=False, nullable=False
    )
    op.execute("UPDATE consent SET conflicts_with_gpc = false")
    op.alter_column(
        "consent",
        "conflicts_with_gpc",
        server_default="f",
        default=False,
        nullable=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("consent", "conflicts_with_gpc")
    op.drop_column("consent", "has_gpc_flag")
    # ### end Alembic commands ###
