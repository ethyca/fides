"""cascade delete tcf_version_hash_history on experience config delete

Revision ID: c8d4e2f6a9b1
Revises: b6d4f8e2c1a3
Create Date: 2026-05-20 12:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c8d4e2f6a9b1"
down_revision = "b6d4f8e2c1a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "tcf_version_hash_history_privacy_experience_config_id_fkey",
        "tcf_version_hash_history",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "tcf_version_hash_history_privacy_experience_config_id_fkey",
        "tcf_version_hash_history",
        "privacyexperienceconfig",
        ["privacy_experience_config_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "tcf_version_hash_history_privacy_experience_config_id_fkey",
        "tcf_version_hash_history",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "tcf_version_hash_history_privacy_experience_config_id_fkey",
        "tcf_version_hash_history",
        "privacyexperienceconfig",
        ["privacy_experience_config_id"],
        ["id"],
    )
