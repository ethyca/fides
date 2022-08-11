"""prepend tables with ctl

Revision ID: aaa81d97a6f6
Revises: f53e04e5b7f5
Create Date: 2022-08-11 09:59:38.709501

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "aaa81d97a6f6"
down_revision = "f53e04e5b7f5"
branch_labels = None
depends_on = None


def upgrade():

    op.rename_table("data_categories", "ctl_data_categories")
    op.rename_table("data_subjects", "ctl_data_subjects")
    op.rename_table("data_uses", "ctl_data_uses")
    op.rename_table("data_qualifiers", "ctl_data_qualifiers")
    op.rename_table("datasets", "ctl_datasets")
    op.rename_table("evaluations", "ctl_evaluations")
    op.rename_table("organizations", "ctl_organizations")
    op.rename_table("policies", "ctl_policies")
    op.rename_table("registries", "ctl_registries")
    op.rename_table("systems", "ctl_systems")


def downgrade():

    op.rename_table("ctl_data_categories", "data_categories")
    op.rename_table("ctl_data_subjects", "data_subjects")
    op.rename_table("ctl_data_uses", "data_uses")
    op.rename_table("ctl_data_qualifiers", "data_qualifiers")
    op.rename_table("ctl_datasets", "datasets")
    op.rename_table("ctl_evaluations", "evaluations")
    op.rename_table("ctl_organizations", "organizations")
    op.rename_table("ctl_policies", "policies")
    op.rename_table("ctl_registries", "registries")
    op.rename_table("ctl_systems", "systems")
