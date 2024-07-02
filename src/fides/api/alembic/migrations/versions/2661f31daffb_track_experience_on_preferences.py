"""track experience on preferences

Revision ID: 2661f31daffb
Revises: b546ce845e6c
Create Date: 2023-05-16 20:05:29.478005

"""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "2661f31daffb"
down_revision = "b546ce845e6c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "anonymized_ip_address",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("method", sa.String(), nullable=True)
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
    op.drop_column("privacypreferencehistory", "method")
    op.drop_column("privacypreferencehistory", "anonymized_ip_address")
