"""migrate_custom_reports

Revision ID: 13f59b9011d6
Revises: c90d46f6d3f2
Create Date: 2024-12-17 20:26:53.847681

"""

from alembic import op

from fides.api.alembic.migrations.helpers.custom_report_migration_functions import (
    downgrade_custom_reports,
    upgrade_custom_reports,
)

# revision identifiers, used by Alembic.
revision = "13f59b9011d6"
down_revision = "c90d46f6d3f2"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    upgrade_custom_reports(connection)


def downgrade():
    connection = op.get_bind()
    downgrade_custom_reports(connection)
