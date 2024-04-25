"""add tags as part of fideslang 1.1.0

Revision ID: d8f8bd52754f
Revises: be432bd23596
Create Date: 2022-07-07 02:54:13.724757

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d8f8bd52754f"
down_revision = "be432bd23596"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "data_categories",
        sa.Column("tags", postgresql.ARRAY(sa.VARCHAR()), nullable=True),
    )
    op.add_column(
        "data_qualifiers",
        sa.Column("tags", postgresql.ARRAY(sa.VARCHAR()), nullable=True),
    )
    op.add_column(
        "data_subjects",
        sa.Column("tags", postgresql.ARRAY(sa.VARCHAR()), nullable=True),
    )
    op.add_column(
        "data_uses", sa.Column("tags", postgresql.ARRAY(sa.VARCHAR()), nullable=True)
    )
    op.add_column(
        "datasets", sa.Column("tags", postgresql.ARRAY(sa.VARCHAR()), nullable=True)
    )
    op.add_column(
        "organizations",
        sa.Column("tags", postgresql.ARRAY(sa.VARCHAR()), nullable=True),
    )
    op.add_column(
        "policies", sa.Column("tags", postgresql.ARRAY(sa.VARCHAR()), nullable=True)
    )
    op.add_column(
        "registries", sa.Column("tags", postgresql.ARRAY(sa.VARCHAR()), nullable=True)
    )
    op.add_column(
        "systems", sa.Column("tags", postgresql.ARRAY(sa.VARCHAR()), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("systems", "tags")
    op.drop_column("registries", "tags")
    op.drop_column("policies", "tags")
    op.drop_column("organizations", "tags")
    op.drop_column("datasets", "tags")
    op.drop_column("data_uses", "tags")
    op.drop_column("data_subjects", "tags")
    op.drop_column("data_qualifiers", "tags")
    op.drop_column("data_categories", "tags")
    # ### end Alembic commands ###
