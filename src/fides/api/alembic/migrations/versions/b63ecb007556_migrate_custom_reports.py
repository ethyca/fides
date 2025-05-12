"""migrate custom reports

Revision ID: b63ecb007556
Revises: e5ec30dfcd87
Create Date: 2024-12-18 20:33:19.961641

"""

from alembic import op

from fides.api.alembic.migrations.helpers.custom_report_migration_functions import (
    downgrade_custom_reports,
    upgrade_custom_reports,
)

# revision identifiers, used by Alembic.
revision = "b63ecb007556"
down_revision = "e5ec30dfcd87"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    upgrade_custom_reports(connection)


def downgrade():
    connection = op.get_bind()
    downgrade_custom_reports(connection)
