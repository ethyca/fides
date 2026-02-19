"""add resurface_behavior to experience config

Revision ID: ea20059aee77
Revises: cc9a5690f9e7
Create Date: 2026-01-13 19:34:06.296198

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision = 'ea20059aee77'
down_revision = 'cc9a5690f9e7'
branch_labels = None
depends_on = None


def upgrade():
    # Create the resurface behavior enum type
    op.execute(
        "CREATE TYPE resurfacebehavior AS ENUM ('reject', 'dismiss')"
    )

    # Add resurface_behavior array column to all three experience config tables
    op.add_column(
        "experienceconfigtemplate",
        sa.Column(
            "resurface_behavior",
            ARRAY(sa.Enum("reject", "dismiss", name="resurfacebehavior")),
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "resurface_behavior",
            ARRAY(sa.Enum("reject", "dismiss", name="resurfacebehavior")),
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column(
            "resurface_behavior",
            ARRAY(sa.Enum("reject", "dismiss", name="resurfacebehavior")),
            nullable=True,
        ),
    )


def downgrade():
    # Remove resurface_behavior column from all three tables (reverse order)
    op.drop_column("privacyexperienceconfighistory", "resurface_behavior")
    op.drop_column("privacyexperienceconfig", "resurface_behavior")
    op.drop_column("experienceconfigtemplate", "resurface_behavior")
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS resurfacebehavior")
