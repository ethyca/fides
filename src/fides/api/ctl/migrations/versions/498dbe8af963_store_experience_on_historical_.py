"""store experience on historical preference

Revision ID: 498dbe8af963
Revises: b546ce845e6c
Create Date: 2023-05-15 20:54:13.623611

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "498dbe8af963"
down_revision = "b546ce845e6c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacypreferencehistory",
        sa.Column("anonymized_ip_address", sa.String(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("privacy_experience_config_history_id", sa.String(), nullable=True),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column("privacy_experience_history_id", sa.String(), nullable=True),
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_privacy_experience_config_history_id"),
        "privacypreferencehistory",
        ["privacy_experience_config_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_privacy_experience_history_id"),
        "privacypreferencehistory",
        ["privacy_experience_history_id"],
        unique=False,
    )
    op.create_foreign_key(
        "privacypreferencehistory_privacy_experience_history_id_fkey",
        "privacypreferencehistory",
        "privacyexperiencehistory",
        ["privacy_experience_history_id"],
        ["id"],
    )
    op.create_foreign_key(
        "privacypreferencehistory_privacy_experience_config_history_fkey",
        "privacypreferencehistory",
        "privacyexperienceconfighistory",
        ["privacy_experience_config_history_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "privacypreferencehistory_privacy_experience_history_id_fkey",
        "privacypreferencehistory",
        type_="foreignkey",
    )
    op.drop_constraint(
        "privacypreferencehistory_privacy_experience_config_history_fkey",
        "privacypreferencehistory",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_privacy_experience_history_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_privacy_experience_config_history_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "privacy_experience_history_id")
    op.drop_column("privacypreferencehistory", "privacy_experience_config_history_id")
    op.drop_column("privacypreferencehistory", "anonymized_ip_address")
