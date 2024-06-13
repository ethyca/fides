"""split privacy experience table

Revision ID: b546ce845e6c
Revises: fc04e3e637c0
Create Date: 2023-05-11 16:21:13.825649

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b546ce845e6c"
down_revision = "fc04e3e637c0"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("delete from privacyexperiencehistory;")
    op.execute("delete from privacyexperience;")
    op.create_table(
        "privacyexperienceconfig",
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
        sa.Column("acknowledgement_button_label", sa.String(), nullable=True),
        sa.Column("banner_title", sa.String(), nullable=True),
        sa.Column("banner_description", sa.String(), nullable=True),
        sa.Column("component", sa.String(), nullable=False),
        sa.Column("component_title", sa.String(), nullable=True),
        sa.Column("component_description", sa.String(), nullable=True),
        sa.Column("confirmation_button_label", sa.String(), nullable=True),
        sa.Column("delivery_mechanism", sa.String(), nullable=False),
        sa.Column("disabled", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("link_label", sa.String(), nullable=True),
        sa.Column("reject_button_label", sa.String(), nullable=True),
        sa.Column("version", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_privacyexperienceconfig_component"),
        "privacyexperienceconfig",
        ["component"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperienceconfig_delivery_mechanism"),
        "privacyexperienceconfig",
        ["delivery_mechanism"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperienceconfig_id"),
        "privacyexperienceconfig",
        ["id"],
        unique=False,
    )
    op.create_table(
        "privacyexperienceconfighistory",
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
        sa.Column("acknowledgement_button_label", sa.String(), nullable=True),
        sa.Column("banner_title", sa.String(), nullable=True),
        sa.Column("banner_description", sa.String(), nullable=True),
        sa.Column("component", sa.String(), nullable=False),
        sa.Column("component_title", sa.String(), nullable=True),
        sa.Column("component_description", sa.String(), nullable=True),
        sa.Column("confirmation_button_label", sa.String(), nullable=True),
        sa.Column("delivery_mechanism", sa.String(), nullable=False),
        sa.Column("disabled", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("link_label", sa.String(), nullable=True),
        sa.Column("reject_button_label", sa.String(), nullable=True),
        sa.Column("version", sa.Float(), nullable=False),
        sa.Column("experience_config_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["experience_config_id"],
            ["privacyexperienceconfig.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_privacyexperienceconfighistory_component"),
        "privacyexperienceconfighistory",
        ["component"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperienceconfighistory_delivery_mechanism"),
        "privacyexperienceconfighistory",
        ["delivery_mechanism"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperienceconfighistory_id"),
        "privacyexperienceconfighistory",
        ["id"],
        unique=False,
    )
    op.drop_index(
        "ix_privacyexperiencetemplate_id", table_name="privacyexperiencetemplate"
    )
    op.drop_index(
        "ix_privacyexperiencetemplate_regions", table_name="privacyexperiencetemplate"
    )
    op.add_column("privacyexperience", sa.Column("region", sa.String(), nullable=False))
    op.add_column(
        "privacyexperience",
        sa.Column("experience_config_id", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperience",
        sa.Column("experience_config_history_id", sa.String(), nullable=True),
    )
    op.drop_index("ix_privacyexperience_regions", table_name="privacyexperience")
    op.create_index(
        op.f("ix_privacyexperience_experience_config_history_id"),
        "privacyexperience",
        ["experience_config_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperience_experience_config_id"),
        "privacyexperience",
        ["experience_config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperience_region"),
        "privacyexperience",
        ["region"],
        unique=False,
    )
    op.create_unique_constraint(
        "region_component", "privacyexperience", ["region", "component"]
    )
    op.drop_constraint(
        "privacyexperience_privacy_experience_template_id_fkey",
        "privacyexperience",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "privacyexperience_experience_config_history_id_fkey",
        "privacyexperience",
        "privacyexperienceconfighistory",
        ["experience_config_history_id"],
        ["id"],
    )
    op.create_foreign_key(
        "privacyexperience_experience_config_id_fkey",
        "privacyexperience",
        "privacyexperienceconfig",
        ["experience_config_id"],
        ["id"],
    )
    op.drop_column("privacyexperience", "banner_description")
    op.drop_column("privacyexperience", "confirmation_button_label")
    op.drop_column("privacyexperience", "component_description")
    op.drop_column("privacyexperience", "banner_title")
    op.drop_column("privacyexperience", "acknowledgement_button_label")
    op.drop_column("privacyexperience", "reject_button_label")
    op.drop_column("privacyexperience", "component_title")
    op.drop_column("privacyexperience", "privacy_experience_template_id")
    op.drop_column("privacyexperience", "regions")
    op.drop_column("privacyexperience", "link_label")
    op.add_column(
        "privacyexperiencehistory", sa.Column("region", sa.String(), nullable=False)
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column("experience_config_id", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column("experience_config_history_id", sa.String(), nullable=True),
    )
    op.drop_index(
        "ix_privacyexperiencehistory_regions", table_name="privacyexperiencehistory"
    )
    op.create_index(
        op.f("ix_privacyexperiencehistory_experience_config_history_id"),
        "privacyexperiencehistory",
        ["experience_config_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperiencehistory_experience_config_id"),
        "privacyexperiencehistory",
        ["experience_config_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperiencehistory_privacy_experience_id"),
        "privacyexperiencehistory",
        ["privacy_experience_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperiencehistory_region"),
        "privacyexperiencehistory",
        ["region"],
        unique=False,
    )
    op.drop_constraint(
        "privacyexperiencehistory_privacy_experience_template_id_fkey",
        "privacyexperiencehistory",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "privacyexperiencehistory_experience_config_id_fkey",
        "privacyexperiencehistory",
        "privacyexperienceconfig",
        ["experience_config_id"],
        ["id"],
    )
    op.create_foreign_key(
        "privacyexperiencehistory_experience_config_history_id_fkey",
        "privacyexperiencehistory",
        "privacyexperienceconfighistory",
        ["experience_config_history_id"],
        ["id"],
    )
    op.drop_column("privacyexperiencehistory", "banner_description")
    op.drop_column("privacyexperiencehistory", "confirmation_button_label")
    op.drop_column("privacyexperiencehistory", "component_description")
    op.drop_column("privacyexperiencehistory", "banner_title")
    op.drop_column("privacyexperiencehistory", "acknowledgement_button_label")
    op.drop_column("privacyexperiencehistory", "reject_button_label")
    op.drop_column("privacyexperiencehistory", "component_title")
    op.drop_column("privacyexperiencehistory", "privacy_experience_template_id")
    op.drop_column("privacyexperiencehistory", "regions")
    op.drop_column("privacyexperiencehistory", "link_label")
    op.drop_table("privacyexperiencetemplate")


def downgrade():
    op.add_column(
        "privacyexperiencehistory",
        sa.Column("link_label", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column(
            "regions",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column(
            "privacy_experience_template_id",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column("component_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column(
            "reject_button_label", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column(
            "acknowledgement_button_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column("banner_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column(
            "component_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column(
            "confirmation_button_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperiencehistory",
        sa.Column(
            "banner_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.drop_constraint(
        "privacyexperiencehistory_experience_config_id_fkey",
        "privacyexperiencehistory",
        type_="foreignkey",
    )
    op.drop_constraint(
        "privacyexperiencehistory_experience_config_history_id_fkey",
        "privacyexperiencehistory",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_privacyexperiencehistory_region"),
        table_name="privacyexperiencehistory",
    )
    op.drop_index(
        op.f("ix_privacyexperiencehistory_privacy_experience_id"),
        table_name="privacyexperiencehistory",
    )
    op.drop_index(
        op.f("ix_privacyexperiencehistory_experience_config_id"),
        table_name="privacyexperiencehistory",
    )
    op.drop_index(
        op.f("ix_privacyexperiencehistory_experience_config_history_id"),
        table_name="privacyexperiencehistory",
    )
    op.create_index(
        "ix_privacyexperiencehistory_regions",
        "privacyexperiencehistory",
        ["regions"],
        unique=False,
    )
    op.drop_column("privacyexperiencehistory", "experience_config_history_id")
    op.drop_column("privacyexperiencehistory", "experience_config_id")
    op.drop_column("privacyexperiencehistory", "region")
    op.add_column(
        "privacyexperience",
        sa.Column("link_label", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperience",
        sa.Column(
            "regions",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperience",
        sa.Column(
            "privacy_experience_template_id",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperience",
        sa.Column("component_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperience",
        sa.Column(
            "reject_button_label", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperience",
        sa.Column(
            "acknowledgement_button_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperience",
        sa.Column("banner_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperience",
        sa.Column(
            "component_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperience",
        sa.Column(
            "confirmation_button_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperience",
        sa.Column(
            "banner_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.drop_constraint(
        "privacyexperience_experience_config_id_fkey",
        "privacyexperience",
        type_="foreignkey",
    )
    op.drop_constraint(
        "privacyexperience_experience_config_history_id_fkey",
        "privacyexperience",
        type_="foreignkey",
    )

    op.drop_constraint("region_component", "privacyexperience", type_="unique")
    op.drop_index(op.f("ix_privacyexperience_region"), table_name="privacyexperience")
    op.drop_index(
        op.f("ix_privacyexperience_experience_config_id"),
        table_name="privacyexperience",
    )
    op.drop_index(
        op.f("ix_privacyexperience_experience_config_history_id"),
        table_name="privacyexperience",
    )
    op.create_index(
        "ix_privacyexperience_regions", "privacyexperience", ["regions"], unique=False
    )
    op.drop_column("privacyexperience", "experience_config_history_id")
    op.drop_column("privacyexperience", "experience_config_id")
    op.drop_column("privacyexperience", "region")
    op.create_table(
        "privacyexperiencetemplate",
        sa.Column("id", sa.VARCHAR(length=255), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("disabled", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("component", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            "delivery_mechanism", sa.VARCHAR(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "regions",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("component_title", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "component_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
        sa.Column("banner_title", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "banner_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
        sa.Column("link_label", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "confirmation_button_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "reject_button_label", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
        sa.Column(
            "acknowledgement_button_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name="privacyexperiencetemplate_pkey"),
    )
    op.create_index(
        "ix_privacyexperiencetemplate_regions",
        "privacyexperiencetemplate",
        ["regions"],
        unique=False,
    )
    op.create_index(
        "ix_privacyexperiencetemplate_id",
        "privacyexperiencetemplate",
        ["id"],
        unique=False,
    )
    op.drop_index(
        op.f("ix_privacyexperienceconfighistory_id"),
        table_name="privacyexperienceconfighistory",
    )
    op.drop_index(
        op.f("ix_privacyexperienceconfighistory_delivery_mechanism"),
        table_name="privacyexperienceconfighistory",
    )
    op.drop_index(
        op.f("ix_privacyexperienceconfighistory_component"),
        table_name="privacyexperienceconfighistory",
    )
    op.drop_table("privacyexperienceconfighistory")
    op.drop_index(
        op.f("ix_privacyexperienceconfig_id"), table_name="privacyexperienceconfig"
    )
    op.drop_index(
        op.f("ix_privacyexperienceconfig_delivery_mechanism"),
        table_name="privacyexperienceconfig",
    )
    op.drop_index(
        op.f("ix_privacyexperienceconfig_component"),
        table_name="privacyexperienceconfig",
    )
    op.drop_table("privacyexperienceconfig")
    op.create_foreign_key(
        "privacyexperiencehistory_privacy_experience_template_id_fkey",
        "privacyexperiencehistory",
        "privacyexperiencetemplate",
        ["privacy_experience_template_id"],
        ["id"],
    )
    op.create_foreign_key(
        "privacyexperience_privacy_experience_template_id_fkey",
        "privacyexperience",
        "privacyexperiencetemplate",
        ["privacy_experience_template_id"],
        ["id"],
    )
