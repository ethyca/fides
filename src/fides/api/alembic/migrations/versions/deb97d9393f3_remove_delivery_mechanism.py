"""remove delivery mechanism

Revision ID: deb97d9393f3
Revises: ed46521679fb
Create Date: 2023-05-25 16:47:16.566034

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "deb97d9393f3"
down_revision = "ed46521679fb"
branch_labels = None
depends_on = None


def upgrade():
    """Remove required delivery mechanism field and rename/add a lot of new fields related to experience configs"""
    op.drop_index(
        "ix_privacyexperienceconfig_delivery_mechanism",
        table_name="privacyexperienceconfig",
    )
    op.drop_index(
        "ix_privacyexperienceconfighistory_delivery_mechanism",
        table_name="privacyexperienceconfighistory",
    )

    op.drop_column("privacyexperienceconfig", "delivery_mechanism")
    op.drop_column("privacyexperienceconfighistory", "delivery_mechanism")

    op.drop_column("privacyexperience", "delivery_mechanism")
    op.drop_column("privacyexperiencehistory", "delivery_mechanism")

    op.drop_column("privacyexperienceconfig", "acknowledgement_button_label")
    op.drop_column("privacyexperienceconfig", "banner_description")
    op.drop_column("privacyexperienceconfig", "banner_title")
    op.drop_column("privacyexperienceconfig", "component_title")
    op.drop_column("privacyexperienceconfig", "component_description")
    op.drop_column("privacyexperienceconfig", "confirmation_button_label")
    op.drop_column("privacyexperienceconfig", "link_label")

    op.add_column(
        "privacyexperienceconfig",
        sa.Column("accept_button_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("acknowledge_button_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("banner_enabled", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig", sa.Column("description", sa.String(), nullable=True)
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("privacy_preferences_link_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("privacy_policy_link_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("privacy_policy_url", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("save_button_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig", sa.Column("title", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_privacyexperienceconfig_banner_enabled"),
        "privacyexperienceconfig",
        ["banner_enabled"],
        unique=False,
    )

    op.drop_column("privacyexperienceconfighistory", "acknowledgement_button_label")
    op.drop_column("privacyexperienceconfighistory", "banner_description")
    op.drop_column("privacyexperienceconfighistory", "banner_title")
    op.drop_column("privacyexperienceconfighistory", "component_description")
    op.drop_column("privacyexperienceconfighistory", "confirmation_button_label")
    op.drop_column("privacyexperienceconfighistory", "component_title")
    op.drop_column("privacyexperienceconfighistory", "link_label")

    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("accept_button_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("acknowledge_button_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("banner_enabled", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("description", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("privacy_preferences_link_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("privacy_policy_link_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("privacy_policy_url", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("save_button_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory", sa.Column("title", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_privacyexperienceconfighistory_banner_enabled"),
        "privacyexperienceconfighistory",
        ["banner_enabled"],
        unique=False,
    )


def downgrade():
    op.add_column(
        "privacyexperiencehistory",
        sa.Column(
            "delivery_mechanism", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("component_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column(
            "acknowledgement_button_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column(
            "confirmation_button_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column(
            "component_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("link_label", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column(
            "delivery_mechanism", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("banner_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column(
            "banner_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.drop_index(
        op.f("ix_privacyexperienceconfighistory_banner_enabled"),
        table_name="privacyexperienceconfighistory",
    )
    op.create_index(
        "ix_privacyexperienceconfighistory_delivery_mechanism",
        "privacyexperienceconfighistory",
        ["delivery_mechanism"],
        unique=False,
    )

    op.drop_column("privacyexperienceconfighistory", "title")
    op.drop_column("privacyexperienceconfighistory", "save_button_label")
    op.drop_column("privacyexperienceconfighistory", "privacy_policy_url")
    op.drop_column("privacyexperienceconfighistory", "privacy_policy_link_label")
    op.drop_column("privacyexperienceconfighistory", "privacy_preferences_link_label")
    op.drop_column("privacyexperienceconfighistory", "description")
    op.drop_column("privacyexperienceconfighistory", "banner_enabled")
    op.drop_column("privacyexperienceconfighistory", "acknowledge_button_label")
    op.drop_column("privacyexperienceconfighistory", "accept_button_label")

    op.add_column(
        "privacyexperienceconfig",
        sa.Column("component_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "acknowledgement_button_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "confirmation_button_label",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "component_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("link_label", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "delivery_mechanism", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("banner_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "banner_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.drop_index(
        op.f("ix_privacyexperienceconfig_banner_enabled"),
        table_name="privacyexperienceconfig",
    )
    op.create_index(
        "ix_privacyexperienceconfig_delivery_mechanism",
        "privacyexperienceconfig",
        ["delivery_mechanism"],
        unique=False,
    )

    op.drop_column("privacyexperienceconfig", "title")
    op.drop_column("privacyexperienceconfig", "save_button_label")
    op.drop_column("privacyexperienceconfig", "privacy_policy_url")
    op.drop_column("privacyexperienceconfig", "privacy_policy_link_label")
    op.drop_column("privacyexperienceconfig", "privacy_preferences_link_label")
    op.drop_column("privacyexperienceconfig", "description")
    op.drop_column("privacyexperienceconfig", "banner_enabled")
    op.drop_column("privacyexperienceconfig", "acknowledge_button_label")
    op.drop_column("privacyexperienceconfig", "accept_button_label")
    op.add_column(
        "privacyexperience",
        sa.Column(
            "delivery_mechanism", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
