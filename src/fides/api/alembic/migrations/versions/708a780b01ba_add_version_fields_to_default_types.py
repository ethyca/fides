"""add version fields to default types

Revision ID: 708a780b01ba
Revises: 3038667ba898
Create Date: 2023-08-17 12:29:04.855626

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "708a780b01ba"
down_revision = "093bb28a8270"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "ctl_data_categories", sa.Column("version_added", sa.Text(), nullable=True)
    )
    op.add_column(
        "ctl_data_categories", sa.Column("version_deprecated", sa.Text(), nullable=True)
    )
    op.add_column(
        "ctl_data_categories", sa.Column("replaced_by", sa.Text(), nullable=True)
    )
    op.add_column(
        "ctl_data_qualifiers", sa.Column("version_added", sa.Text(), nullable=True)
    )
    op.add_column(
        "ctl_data_qualifiers", sa.Column("version_deprecated", sa.Text(), nullable=True)
    )
    op.add_column(
        "ctl_data_qualifiers", sa.Column("replaced_by", sa.Text(), nullable=True)
    )
    op.add_column(
        "ctl_data_subjects", sa.Column("version_added", sa.Text(), nullable=True)
    )
    op.add_column(
        "ctl_data_subjects", sa.Column("version_deprecated", sa.Text(), nullable=True)
    )
    op.add_column(
        "ctl_data_subjects", sa.Column("replaced_by", sa.Text(), nullable=True)
    )
    op.add_column("ctl_data_uses", sa.Column("version_added", sa.Text(), nullable=True))
    op.add_column(
        "ctl_data_uses", sa.Column("version_deprecated", sa.Text(), nullable=True)
    )
    op.add_column("ctl_data_uses", sa.Column("replaced_by", sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("ctl_data_uses", "replaced_by")
    op.drop_column("ctl_data_uses", "version_deprecated")
    op.drop_column("ctl_data_uses", "version_added")
    op.drop_column("ctl_data_subjects", "replaced_by")
    op.drop_column("ctl_data_subjects", "version_deprecated")
    op.drop_column("ctl_data_subjects", "version_added")
    op.drop_column("ctl_data_qualifiers", "replaced_by")
    op.drop_column("ctl_data_qualifiers", "version_deprecated")
    op.drop_column("ctl_data_qualifiers", "version_added")
    op.drop_column("ctl_data_categories", "replaced_by")
    op.drop_column("ctl_data_categories", "version_deprecated")
    op.drop_column("ctl_data_categories", "version_added")
    # ### end Alembic commands ###
