"""add notice and exp translations

Revision ID: a1e23b70f2b2
Revises: 26d5976531d6
Create Date: 2024-02-01 21:49:20.792733

"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op
from loguru import logger
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a1e23b70f2b2"
down_revision = "26d5976531d6"
branch_labels = None
depends_on = None


def upgrade():
    logger.info(
        f"Starting Consent Multitranslation Schema Migration (#1) {datetime.now()}"
    )

    op.create_table(
        "experienceconfigtemplate",
        sa.Column("id", sa.String(length=255), nullable=False),
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
        sa.Column("regions", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("component", sa.String(), nullable=False),
        sa.Column("privacy_notice_keys", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "translations",
            postgresql.ARRAY(postgresql.JSONB(astext_type=sa.Text())),
            nullable=True,
        ),
        sa.Column("disabled", sa.Boolean(), nullable=False),
        sa.Column("dismissable", sa.Boolean(), server_default="t", nullable=False),
        sa.Column(
            "auto_detect_language", sa.Boolean(), server_default="t", nullable=False
        ),
        sa.Column(
            "allow_language_selection", sa.Boolean(), server_default="f", nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_experienceconfigtemplate_id"),
        "experienceconfigtemplate",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_experienceconfigtemplate_component"),
        "experienceconfigtemplate",
        ["component"],
        unique=False,
    )
    op.create_table(
        "experiencenotices",
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
        sa.Column("notice_id", sa.String(), nullable=False),
        sa.Column("experience_config_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["experience_config_id"], ["privacyexperienceconfig.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["notice_id"], ["privacynotice.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("notice_id", "experience_config_id"),
    )
    op.create_index(
        op.f("ix_experiencenotices_experience_config_id"),
        "experiencenotices",
        ["experience_config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_experiencenotices_notice_id"),
        "experiencenotices",
        ["notice_id"],
        unique=False,
    )
    op.create_table(
        "experiencetranslation",
        sa.Column("id", sa.String(length=255), nullable=False),
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
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("accept_button_label", sa.String(), nullable=True),
        sa.Column("acknowledge_button_label", sa.String(), nullable=True),
        sa.Column("banner_description", sa.String(), nullable=True),
        sa.Column("banner_title", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("privacy_policy_link_label", sa.String(), nullable=True),
        sa.Column("privacy_policy_url", sa.String(), nullable=True),
        sa.Column("privacy_preferences_link_label", sa.String(), nullable=True),
        sa.Column("reject_button_label", sa.String(), nullable=True),
        sa.Column("save_button_label", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("experience_config_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["experience_config_id"],
            ["privacyexperienceconfig.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "language", "experience_config_id", name="experience_translation"
        ),
    )
    op.create_index(
        op.f("ix_experiencetranslation_id"),
        "experiencetranslation",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_experiencetranslation_experience_config_id"),
        "experiencetranslation",
        ["experience_config_id"],
        unique=False,
    )

    op.create_table(
        "noticetranslation",
        sa.Column("id", sa.String(length=255), nullable=False),
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
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("privacy_notice_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["privacy_notice_id"],
            ["privacynotice.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("language", "privacy_notice_id", name="notice_translation"),
    )
    op.create_index(
        op.f("ix_noticetranslation_id"), "noticetranslation", ["id"], unique=False
    )
    op.drop_constraint("region_component", "privacyexperience", type_="unique")
    op.drop_column("privacyexperience", "component")
    op.add_column(
        "privacyexperienceconfig", sa.Column("origin", sa.String(), nullable=True)
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("dismissable", sa.Boolean(), server_default="t", nullable=False),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "allow_language_selection", sa.Boolean(), server_default="f", nullable=False
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "auto_detect_language", sa.Boolean(), server_default="t", nullable=False
        ),
    )
    op.add_column(
        "privacyexperienceconfig", sa.Column("name", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_privacyexperienceconfig_disabled"),
        "privacyexperienceconfig",
        ["disabled"],
        unique=False,
    )
    op.create_foreign_key(
        "config_template_origin",
        "privacyexperienceconfig",
        "experienceconfigtemplate",
        ["origin"],
        ["id"],
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("language", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory", sa.Column("name", sa.String(), nullable=True)
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("origin", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("dismissable", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("auto_detect_language", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("allow_language_selection", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("translation_id", sa.String(), nullable=True),
    )
    op.create_index(
        op.f("ix_privacyexperienceconfighistory_translation_id"),
        "privacyexperienceconfighistory",
        ["translation_id"],
        unique=False,
    )
    op.alter_column(
        "privacyexperienceconfighistory",
        "experience_config_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.create_foreign_key(
        "confighistory_origin",
        "privacyexperienceconfighistory",
        "experienceconfigtemplate",
        ["origin"],
        ["id"],
    )
    op.create_foreign_key(
        "confighistory_translation_id",
        "privacyexperienceconfighistory",
        "experiencetranslation",
        ["translation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # drop FK constraint between PrivacyExperienceConfigHistory and PrivacyExperienceConfig,
    # to allow us to delete PrivacyExperienceConfigs without removing their associated history records
    op.drop_constraint(
        "privacyexperienceconfighistory_experience_config_id_fkey",
        "privacyexperienceconfighistory",
        type_="foreignkey",
    )
    op.alter_column(
        "privacynotice",
        "regions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        nullable=True,
    )
    op.add_column(
        "privacynoticehistory", sa.Column("language", sa.String(), nullable=True)
    )
    op.add_column(
        "privacynoticehistory",
        sa.Column(
            "title", sa.String(), nullable=True
        ),  # temporarily nullable for existing values
    )
    op.add_column(
        "privacynoticehistory", sa.Column("translation_id", sa.String(), nullable=True)
    )
    op.alter_column(
        "privacynoticehistory",
        "regions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        nullable=True,
    )
    op.alter_column(
        "privacynoticehistory",
        "displayed_in_privacy_center",
        existing_type=sa.BOOLEAN(),
        nullable=True,
    )
    op.alter_column(
        "privacynoticehistory",
        "displayed_in_overlay",
        existing_type=sa.BOOLEAN(),
        nullable=True,
    )
    op.alter_column(
        "privacynoticehistory",
        "displayed_in_api",
        existing_type=sa.BOOLEAN(),
        nullable=True,
    )
    op.alter_column(
        "privacynoticehistory",
        "privacy_notice_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.create_foreign_key(
        "noticehistory_translation_id",
        "privacynoticehistory",
        "noticetranslation",
        ["translation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_privacynoticehistory_translation_id"),
        "privacynoticehistory",
        ["translation_id"],
        unique=False,
    )
    op.add_column(
        "privacynoticetemplate",
        sa.Column(
            "translations",
            postgresql.ARRAY(postgresql.JSONB(astext_type=sa.Text())),
            nullable=True,
        ),
    )
    op.alter_column(
        "privacynoticetemplate",
        "regions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        nullable=True,
    )
    op.drop_index(
        "ix_privacypreferencehistory_privacy_experience_id",
        table_name="privacypreferencehistory",
    )
    op.drop_constraint(
        "privacypreferencehistory_privacy_experience_id_fkey",
        "privacypreferencehistory",
        type_="foreignkey",
    )
    op.add_column(
        "privacypreferencehistory", sa.Column("language", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_language"),
        "privacypreferencehistory",
        ["language"],
        unique=False,
    )
    op.add_column(
        "servednoticehistory", sa.Column("language", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_servednoticehistory_language"),
        "servednoticehistory",
        ["language"],
        unique=False,
    )
    op.drop_index(
        "ix_servednoticehistory_privacy_experience_id", table_name="servednoticehistory"
    )
    op.drop_constraint(
        "servednoticehistory_privacy_experience_id_fkey",
        "servednoticehistory",
        type_="foreignkey",
    )


def downgrade():
    op.create_foreign_key(
        "servednoticehistory_privacy_experience_id_fkey",
        "servednoticehistory",
        "privacyexperience",
        ["privacy_experience_id"],
        ["id"],
    )
    op.create_index(
        "ix_servednoticehistory_privacy_experience_id",
        "servednoticehistory",
        ["privacy_experience_id"],
        unique=False,
    )
    op.drop_index(
        op.f("ix_servednoticehistory_language"), table_name="servednoticehistory"
    )
    op.drop_column("servednoticehistory", "language")
    op.drop_index(
        op.f("ix_privacypreferencehistory_language"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacyexperienceconfighistory_translation_id"),
        table_name="privacyexperienceconfighistory",
    )
    op.drop_column("privacypreferencehistory", "language")
    op.create_foreign_key(
        "privacypreferencehistory_privacy_experience_id_fkey",
        "privacypreferencehistory",
        "privacyexperience",
        ["privacy_experience_id"],
        ["id"],
    )
    op.create_index(
        "ix_privacypreferencehistory_privacy_experience_id",
        "privacypreferencehistory",
        ["privacy_experience_id"],
        unique=False,
    )
    op.alter_column(
        "privacynoticetemplate",
        "regions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        nullable=True,
    )
    op.drop_column("privacynoticetemplate", "translations")
    op.drop_constraint(
        "noticehistory_translation_id", "privacynoticehistory", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_privacynoticehistory_translation_id"),
        table_name="privacynoticehistory",
    )
    op.alter_column(
        "privacynoticehistory",
        "privacy_notice_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.alter_column(
        "privacynoticehistory",
        "regions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        nullable=True,
    )
    op.drop_column("privacynoticehistory", "translation_id")
    op.drop_column("privacynoticehistory", "title")
    op.drop_column("privacynoticehistory", "language")
    op.alter_column(
        "privacynotice",
        "regions",
        existing_type=postgresql.ARRAY(sa.VARCHAR()),
        nullable=True,
    )
    op.drop_constraint(
        "confighistory_translation_id",
        "privacyexperienceconfighistory",
        type_="foreignkey",
    )
    op.drop_constraint(
        "confighistory_origin", "privacyexperienceconfighistory", type_="foreignkey"
    )
    op.alter_column(
        "privacyexperienceconfighistory",
        "experience_config_id",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.drop_column("privacyexperienceconfighistory", "translation_id")
    op.drop_column("privacyexperienceconfighistory", "allow_language_selection")
    op.drop_column("privacyexperienceconfighistory", "auto_detect_language")
    op.drop_column("privacyexperienceconfighistory", "dismissable")
    op.drop_column("privacyexperienceconfighistory", "origin")
    op.drop_column("privacyexperienceconfighistory", "name")
    op.drop_column("privacyexperienceconfighistory", "language")

    op.drop_constraint(
        "config_template_origin", "privacyexperienceconfig", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_privacyexperienceconfig_disabled"),
        table_name="privacyexperienceconfig",
    )
    op.drop_column("privacyexperienceconfig", "name")
    op.drop_column("privacyexperienceconfig", "allow_language_selection")
    op.drop_column("privacyexperienceconfig", "dismissable")
    op.drop_column("privacyexperienceconfig", "auto_detect_language")
    op.drop_column("privacyexperienceconfig", "origin")
    op.add_column(
        "privacyexperience",
        sa.Column("component", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_unique_constraint(
        "region_component", "privacyexperience", ["region", "component"]
    )
    op.drop_index(op.f("ix_noticetranslation_id"), table_name="noticetranslation")
    op.drop_table("noticetranslation")
    op.drop_index(
        op.f("ix_experiencetranslation_id"), table_name="experiencetranslation"
    )
    op.drop_index(
        op.f("ix_experiencetranslation_experience_config_id"),
        table_name="experiencetranslation",
    )
    op.drop_table("experiencetranslation")
    op.drop_index(
        op.f("ix_experiencenotices_notice_id"), table_name="experiencenotices"
    )
    op.drop_index(
        op.f("ix_experiencenotices_experience_config_id"),
        table_name="experiencenotices",
    )
    op.drop_table("experiencenotices")
    op.drop_index(
        op.f("ix_experienceconfigtemplate_id"), table_name="experienceconfigtemplate"
    )
    op.drop_table("experienceconfigtemplate")
