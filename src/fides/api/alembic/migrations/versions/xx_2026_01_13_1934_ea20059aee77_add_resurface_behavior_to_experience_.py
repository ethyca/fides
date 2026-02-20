"""add resurface_behavior to experience config

Revision ID: ea20059aee77
Revises: 29acbb0689de
Create Date: 2026-01-13 19:34:06.296198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea20059aee77'
down_revision = '29acbb0689de'
branch_labels = None
depends_on = None


def upgrade():
    # Add resurface_behavior array column to all three experience config tables
    op.add_column(
        "experienceconfigtemplate",
        sa.Column(
            "resurface_behavior",
            sa.ARRAY(sa.String()),
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "resurface_behavior",
            sa.ARRAY(sa.String()),
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column(
            "resurface_behavior",
            sa.ARRAY(sa.String()),
            nullable=True,
        ),
    )


def downgrade():
    # Remove resurface_behavior column from all three tables (reverse order)
    op.drop_column("privacyexperienceconfighistory", "resurface_behavior")
    op.drop_column("privacyexperienceconfig", "resurface_behavior")
    op.drop_column("experienceconfigtemplate", "resurface_behavior")
