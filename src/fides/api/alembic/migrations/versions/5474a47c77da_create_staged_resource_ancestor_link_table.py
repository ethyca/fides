"""
Creates staged resource ancestor link table.

Does not populate the table with data, that is handled in a separate data migration.

Also does not drop the StagedResource.child_diff_statuses column,
that is handled in a separate migration, _after_ the data migration
that populates the staged resource ancestor link table, to prevent
unintended data loss.

Revision ID: 5474a47c77da
Revises: 440a5b9a3493
Create Date: 2025-05-27 19:02:43.802783

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5474a47c77da"
down_revision = "440a5b9a3493"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "stagedresourceancestor",
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
        sa.Column("ancestor_urn", sa.String(), nullable=False),
        sa.Column("descendant_urn", sa.String(), nullable=False),
        # primary key, foreign key and unique constraints are deferred
        # until after the data migration that populates the table,
        # to avoid slowing down the data migration
    )

    # defer creating `stagedresourceancestor` indexes until after the data migration
    # that populates the table, to avoid slowing down the data migration

    # add an index for StagedResource.diff_status to improve queries against the diff_status field
    op.create_index(
        op.f("ix_stagedresource_diff_status"),
        "stagedresource",
        ["diff_status"],
        unique=False,
    )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    # drop the StagedResource.diff_status index created in the migration
    op.drop_index(op.f("ix_stagedresource_diff_status"), table_name="stagedresource")

    # drop the stagedresourceancestor table (and all its indexes and constraints)
    op.drop_table("stagedresourceancestor")
    # ### end Alembic commands ###
