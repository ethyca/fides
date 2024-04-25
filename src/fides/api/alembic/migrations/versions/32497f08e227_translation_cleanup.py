"""cleanup migration for consent multitranslation.
Removes deprecated fields from privacy notice and privacy experience related tables and adds
some constraints after the previous data migration guarantees

Revision ID: 32497f08e227
Revises: 14acee6f5459
Create Date: 2024-03-05 17:08:07.093568

"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op
from loguru import logger
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "32497f08e227"
down_revision = "14acee6f5459"
branch_labels = None
depends_on = None


def upgrade():
    logger.info(
        f"Starting Consent Multitranslation Schema Migration (#3) {datetime.now()}"
    )

    # Privacy Experience > experience_config_id is guaranteed to exist after the data migration so we can make this non-nullable
    op.alter_column(
        "privacyexperience",
        "experience_config_id",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    # Resetting Experience Config name back to non-nullable after data migration
    op.alter_column(
        "privacyexperienceconfig", "name", existing_type=sa.VARCHAR(), nullable=False
    )
    # Resetting PrivacyNoticeHistory title back to non-nullable after data migration
    op.alter_column(
        "privacynoticehistory",
        "title",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    # Dropping the index as a prereq before removing the column
    op.drop_index(
        "ix_privacyexperienceconfig_banner_enabled",
        table_name="privacyexperienceconfig",
    )
    # Removing the "translatable" columns that have been moved to ExperienceTranslation
    op.drop_column("privacyexperienceconfig", "privacy_policy_url")
    op.drop_column("privacyexperienceconfig", "acknowledge_button_label")
    op.drop_column("privacyexperienceconfig", "description")
    op.drop_column("privacyexperienceconfig", "banner_enabled")
    op.drop_column("privacyexperienceconfig", "banner_description")
    op.drop_column("privacyexperienceconfig", "accept_button_label")
    op.drop_column("privacyexperienceconfig", "privacy_preferences_link_label")
    # The Experience Config no longer stores a version
    op.drop_column("privacyexperienceconfig", "version")
    op.drop_column("privacyexperienceconfig", "banner_title")
    op.drop_column("privacyexperienceconfig", "title")
    op.drop_column("privacyexperienceconfig", "privacy_policy_link_label")
    # New concept by the same name is now stored on the ExperienceTranslatoin table
    op.drop_column("privacyexperienceconfig", "is_default")
    op.drop_column("privacyexperienceconfig", "save_button_label")
    op.drop_column("privacyexperienceconfig", "reject_button_label")
    # The historical config no longer references the current config, but a translation instead
    op.drop_column("privacyexperienceconfighistory", "experience_config_id")
    # Dropping notice regions index as a prereq for deleting the column
    op.drop_index("ix_privacynotice_regions", table_name="privacynotice")
    # Deleting notice constructs that have been moved to the Experience side
    op.drop_column("privacynotice", "displayed_in_api")
    op.drop_column("privacynotice", "description")
    op.drop_column("privacynotice", "regions")
    op.drop_column("privacynotice", "displayed_in_overlay")
    op.drop_column("privacynotice", "displayed_in_privacy_center")
    op.drop_column("privacynotice", "version")
    # Dropping the notice history > notice id FK as a prereq for dropping the column
    op.drop_constraint(
        "privacynoticehistory_privacy_notice_id_fkey",
        "privacynoticehistory",
        type_="foreignkey",
    )
    op.drop_column("privacynoticehistory", "privacy_notice_id")
    # Similarly removing deprecated concepts off the notice templates
    op.drop_index(
        "ix_privacynoticetemplate_regions", table_name="privacynoticetemplate"
    )
    op.drop_column("privacynoticetemplate", "displayed_in_api")
    op.drop_column("privacynoticetemplate", "description")
    op.drop_column("privacynoticetemplate", "regions")
    op.drop_column("privacynoticetemplate", "displayed_in_overlay")
    op.drop_column("privacynoticetemplate", "displayed_in_privacy_center")
    # Removing the reference from privacy preference history and served notice history to the experience
    op.drop_column("privacypreferencehistory", "privacy_experience_id")
    op.drop_column("servednoticehistory", "privacy_experience_id")

    logger.info(f"Consent Multitranslation Migrations Complete {datetime.now()}")


def downgrade():
    """Downgrade edited to make all columns nullable"""
    op.add_column(
        "servednoticehistory",
        sa.Column(
            "privacy_experience_id", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "privacy_experience_id", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacynoticetemplate",
        sa.Column(
            "displayed_in_privacy_center",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacynoticetemplate",
        sa.Column(
            "displayed_in_overlay", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacynoticetemplate",
        sa.Column(
            "regions",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacynoticetemplate",
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacynoticetemplate",
        sa.Column("displayed_in_api", sa.BOOLEAN(), autoincrement=False, nullable=True),
    )
    op.create_index(
        "ix_privacynoticetemplate_regions",
        "privacynoticetemplate",
        ["regions"],
        unique=False,
    )
    op.add_column(
        "privacynoticehistory",
        sa.Column(
            "privacy_notice_id", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.create_foreign_key(
        "privacynoticehistory_privacy_notice_id_fkey",
        "privacynoticehistory",
        "privacynotice",
        ["privacy_notice_id"],
        ["id"],
    )
    op.add_column(
        "privacynotice",
        sa.Column(
            "displayed_in_privacy_center",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacynotice",
        sa.Column(
            "version",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacynotice",
        sa.Column(
            "displayed_in_overlay", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacynotice",
        sa.Column(
            "regions",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacynotice",
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacynotice",
        sa.Column("displayed_in_api", sa.BOOLEAN(), autoincrement=False, nullable=True),
    )
    op.create_index(
        "ix_privacynotice_regions", "privacynotice", ["regions"], unique=False
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column(
            "experience_config_id", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.create_foreign_key(
        "privacyexperienceconfighistory_experience_config_id_fkey",
        "privacyexperienceconfighistory",
        "privacyexperienceconfig",
        ["experience_config_id"],
        ["id"],
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "reject_button_label", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "save_button_label", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("is_default", sa.BOOLEAN(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "privacy_policy_link_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("banner_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "version",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "privacy_preferences_link_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "accept_button_label", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "banner_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("banner_enabled", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "acknowledge_button_label", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "privacy_policy_url", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.create_index(
        "ix_privacyexperienceconfig_banner_enabled",
        "privacyexperienceconfig",
        ["banner_enabled"],
        unique=False,
    )
    op.alter_column(
        "privacyexperienceconfig", "name", existing_type=sa.VARCHAR(), nullable=True
    )
    op.alter_column(
        "privacyexperience",
        "experience_config_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
