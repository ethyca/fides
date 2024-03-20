"""remove cascade delete from property linking table

Revision ID: 7799269e7078
Revises: 2e9aba76c322
Create Date: 2024-03-14 05:53:23.282985

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "7799269e7078"
down_revision = "2e9aba76c322"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "plus_privacy_experience_config_property_property_id_fkey",
        "plus_privacy_experience_config_property",
        type_="foreignkey",
    )
    op.drop_constraint(
        "plus_privacy_experience_confi_privacy_experience_config_id_fkey",
        "plus_privacy_experience_config_property",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "plus_privacy_experience_config_property_property_id_fkey",
        "plus_privacy_experience_config_property",
        "plus_property",
        ["property_id"],
        ["id"],
    )
    op.create_foreign_key(
        "plus_privacy_experience_confi_privacy_experience_config_id_fkey",
        "plus_privacy_experience_config_property",
        "privacyexperienceconfig",
        ["privacy_experience_config_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "plus_privacy_experience_config_property_property_id_fkey",
        "plus_privacy_experience_config_property",
        type_="foreignkey",
    )
    op.drop_constraint(
        "plus_privacy_experience_confi_privacy_experience_config_id_fkey",
        "plus_privacy_experience_config_property",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "plus_privacy_experience_confi_privacy_experience_config_id_fkey",
        "plus_privacy_experience_config_property",
        "privacyexperienceconfig",
        ["privacy_experience_config_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "plus_privacy_experience_config_property_property_id_fkey",
        "plus_privacy_experience_config_property",
        "plus_property",
        ["property_id"],
        ["id"],
        ondelete="CASCADE",
    )
