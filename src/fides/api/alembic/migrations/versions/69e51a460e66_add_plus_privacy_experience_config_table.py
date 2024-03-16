"""add plus_privacy_experience_config table

Revision ID: 69e51a460e66
Revises: 3815b0db5b14
Create Date: 2024-03-01 22:47:59.867223

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "69e51a460e66"
down_revision = "3815b0db5b14"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plus_privacy_experience_config_property",
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
        sa.Column("id", sa.String(length=255), nullable=True),
        sa.Column("privacy_experience_config_id", sa.String(), nullable=False),
        sa.Column("property_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["privacy_experience_config_id"],
            ["privacyexperienceconfig.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["property_id"], ["plus_property.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("privacy_experience_config_id", "property_id"),
    )
    op.create_index(
        op.f("ix_plus_privacy_experience_config_property_privacy_experience_config_id"),
        "plus_privacy_experience_config_property",
        ["privacy_experience_config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_plus_privacy_experience_config_property_property_id"),
        "plus_privacy_experience_config_property",
        ["property_id"],
        unique=False,
    )
    op.drop_index("ix_plus_property_id", table_name="plus_property")


def downgrade():
    op.create_index("ix_plus_property_id", "plus_property", ["id"], unique=False)
    op.drop_index(
        op.f("ix_plus_privacy_experience_config_property_property_id"),
        table_name="plus_privacy_experience_config_property",
    )
    op.drop_index(
        op.f("ix_plus_privacy_experience_config_property_privacy_experience_config_id"),
        table_name="plus_privacy_experience_config_property",
    )
    op.drop_table("plus_privacy_experience_config_property")
