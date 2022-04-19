"""Add created_at and updated_at

Revision ID: 7c851d8a102a
Revises: 45c7a349db68
Create Date: 2021-12-16 12:20:03.801089

"""
from alembic import op
from sqlalchemy import Column, DateTime, text

from fidesapi.sql_models import sql_model_map


# revision identifiers, used by Alembic.
revision = "7c851d8a102a"
down_revision = "312aff72b275"
branch_labels = None
depends_on = None


def upgrade():
    for model in sql_model_map.values():
        op.add_column(
            model.__tablename__,
            Column(
                "created_at",
                DateTime(timezone=True),
                server_default=text("now()"),
                nullable=True,
            ),
        )
        op.add_column(
            model.__tablename__,
            Column(
                "updated_at",
                DateTime(timezone=True),
                server_default=text("now()"),
                nullable=True,
            ),
        )


def downgrade():
    for model in sql_model_map.values():
        op.drop_column(model.__tablename__, "created_at")
        op.drop_column(model.__tablename__, "updated_at")
