"""Add created_at and updated_at

Revision ID: 7c851d8a102a
Revises: 45c7a349db68
Create Date: 2021-12-16 12:20:03.801089

"""

from alembic import op
from sqlalchemy import Column, DateTime, text

from fides.api.models.sql_models import sql_model_map

# revision identifiers, used by Alembic.
revision = "7c851d8a102a"
down_revision = "312aff72b275"
branch_labels = None
depends_on = None

SQL_MODEL_LIST = [
    "data_categories",
    "data_qualifiers",
    "data_uses",
    "data_subjects",
    "datasets",
    "evaluations",
    "policies",
    "registries",
    "systems",
    "organizations",
]


def upgrade():
    for table_name in SQL_MODEL_LIST:
        op.add_column(
            table_name,
            Column(
                "created_at",
                DateTime(timezone=True),
                server_default=text("now()"),
                nullable=True,
            ),
        )
        op.add_column(
            table_name,
            Column(
                "updated_at",
                DateTime(timezone=True),
                server_default=text("now()"),
                nullable=True,
            ),
        )


def downgrade():
    for table_name in SQL_MODEL_LIST:
        op.drop_column(table_name, "created_at")
        op.drop_column(table_name, "updated_at")
