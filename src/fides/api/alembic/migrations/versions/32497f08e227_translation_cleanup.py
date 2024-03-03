"""translation_cleanup Cleans up deprecated tables and fields after multitranslation migration

Revision ID: 32497f08e227
Revises: 0c65325843bd
Create Date: 2024-03-01 22:02:51.248873

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "32497f08e227"
down_revision = "0c65325843bd"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("privacypreferencehistory", "privacy_experience_id")
    op.drop_column("servednoticehistory", "privacy_experience_id")

    op.drop_index(
        "ix_privacyexperienceconfig_banner_enabled",
        table_name="privacyexperienceconfig",
    )
    op.drop_column("privacyexperienceconfig", "description")
    op.drop_column("privacyexperienceconfig", "banner_enabled")
    op.drop_column("privacyexperienceconfig", "title")
    op.drop_column("privacyexperienceconfig", "is_default")
    op.drop_column("privacyexperienceconfig", "accept_button_label")
    op.drop_column("privacyexperienceconfig", "version")
    op.drop_column("privacyexperienceconfig", "reject_button_label")
    op.drop_column("privacyexperienceconfig", "banner_title")
    op.drop_column("privacyexperienceconfig", "privacy_preferences_link_label")
    op.drop_column("privacyexperienceconfig", "privacy_policy_link_label")
    op.drop_column("privacyexperienceconfig", "privacy_policy_url")
    op.drop_column("privacyexperienceconfig", "acknowledge_button_label")
    op.drop_column("privacyexperienceconfig", "banner_description")
    op.drop_column("privacyexperienceconfig", "save_button_label")
    op.drop_index(
        "ix_privacyexperienceconfighistory_banner_enabled",
        table_name="privacyexperienceconfighistory",
    )
    op.drop_column("privacyexperienceconfighistory", "banner_enabled")
    op.drop_column("privacyexperienceconfighistory", "experience_config_id")
    op.drop_index("ix_privacynotice_regions", table_name="privacynotice")
    op.drop_column("privacynotice", "description")
    op.drop_column("privacynotice", "version")
    op.drop_column("privacynotice", "displayed_in_privacy_center")
    op.drop_column("privacynotice", "regions")
    op.drop_column("privacynotice", "displayed_in_overlay")
    op.drop_column("privacynotice", "displayed_in_api")
    op.drop_index("ix_privacynoticehistory_regions", table_name="privacynoticehistory")
    op.drop_constraint(
        "privacynoticehistory_privacy_notice_id_fkey",
        "privacynoticehistory",
        type_="foreignkey",
    )
    op.drop_column("privacynoticehistory", "privacy_notice_id")
    op.drop_column("privacynoticehistory", "displayed_in_privacy_center")
    op.drop_column("privacynoticehistory", "displayed_in_overlay")
    op.drop_column("privacynoticehistory", "regions")
    op.drop_column("privacynoticehistory", "displayed_in_api")
    op.drop_index(
        "ix_privacynoticetemplate_regions", table_name="privacynoticetemplate"
    )
    op.drop_column("privacynoticetemplate", "description")
    op.drop_column("privacynoticetemplate", "displayed_in_privacy_center")
    op.drop_column("privacynoticetemplate", "regions")
    op.drop_column("privacynoticetemplate", "displayed_in_overlay")
    op.drop_column("privacynoticetemplate", "displayed_in_api")

    # Resetting PrivacyExperienceConfigHistory language back to non-nullable after data migration
    op.alter_column(
        "privacyexperienceconfighistory",
        "language",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )

    # Resetting PrivacyNoticeHistory language back to non-nullable after data migration
    op.alter_column(
        "privacynoticehistory",
        "title",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )

    # Resetting PrivacyNoticeHistory title back to non-nullable after data migration
    op.alter_column(
        "privacynoticehistory",
        "title",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )

    # Previous data migration deleted Experience Configs and Experiences so we have a reset state - moving forward, this FK should exist
    op.alter_column(
        "privacyexperience",
        "experience_config_id",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )

    op.alter_column(
        "experienceconfigtemplate", "name", existing_type=sa.VARCHAR(), nullable=False
    )
    op.alter_column(
        "privacyexperienceconfig", "name", existing_type=sa.VARCHAR(), nullable=False
    )


def downgrade():
    op.alter_column(
        "privacyexperienceconfig", "name", existing_type=sa.VARCHAR(), nullable=True
    )
    op.alter_column(
        "experienceconfigtemplate", "name", existing_type=sa.VARCHAR(), nullable=True
    )

    op.alter_column(
        "privacyexperience",
        "experience_config_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )

    op.add_column(
        "privacynoticetemplate",
        sa.Column(
            "displayed_in_api", sa.BOOLEAN(), autoincrement=False, nullable=False
        ),
    )
    op.add_column(
        "privacynoticetemplate",
        sa.Column(
            "displayed_in_overlay", sa.BOOLEAN(), autoincrement=False, nullable=False
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
        sa.Column(
            "displayed_in_privacy_center",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "privacynoticetemplate",
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
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
            "displayed_in_api", sa.BOOLEAN(), autoincrement=False, nullable=False
        ),
    )
    op.add_column(
        "privacynoticehistory",
        sa.Column(
            "regions",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacynoticehistory",
        sa.Column(
            "displayed_in_overlay", sa.BOOLEAN(), autoincrement=False, nullable=False
        ),
    )
    op.add_column(
        "privacynoticehistory",
        sa.Column(
            "displayed_in_privacy_center",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=False,
        ),
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
    op.create_index(
        "ix_privacynoticehistory_regions",
        "privacynoticehistory",
        ["regions"],
        unique=False,
    )
    op.add_column(
        "privacynotice",
        sa.Column(
            "displayed_in_api", sa.BOOLEAN(), autoincrement=False, nullable=False
        ),
    )
    op.add_column(
        "privacynotice",
        sa.Column(
            "displayed_in_overlay", sa.BOOLEAN(), autoincrement=False, nullable=False
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
        sa.Column(
            "displayed_in_privacy_center",
            sa.BOOLEAN(),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "privacynotice",
        sa.Column(
            "version",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "privacynotice",
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
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
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("banner_enabled", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_index(
        "ix_privacyexperienceconfighistory_banner_enabled",
        "privacyexperienceconfighistory",
        ["banner_enabled"],
        unique=False,
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "save_button_label", sa.VARCHAR(), autoincrement=False, nullable=True
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
        sa.Column(
            "privacy_preferences_link_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("banner_title", sa.VARCHAR(), autoincrement=False, nullable=True),
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
            "version",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
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
        sa.Column("is_default", sa.BOOLEAN(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("banner_enabled", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_index(
        "ix_privacyexperienceconfig_banner_enabled",
        "privacyexperienceconfig",
        ["banner_enabled"],
        unique=False,
    )
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
