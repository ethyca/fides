"""remove delivery mechanism

Revision ID: 931fd6b4aea7
Revises: 8a71872089e4
Create Date: 2023-05-23 17:45:43.479032

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "931fd6b4aea7"
down_revision = "8a71872089e4"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index(
        "ix_privacyexperienceconfig_delivery_mechanism",
        table_name="privacyexperienceconfig",
    )
    op.drop_index(
        "ix_privacyexperienceconfighistory_delivery_mechanism",
        table_name="privacyexperienceconfighistory",
    )

    op.drop_column("privacyexperience", "delivery_mechanism")
    op.drop_column("privacyexperiencehistory", "delivery_mechanism")

    op.drop_column("privacyexperienceconfig", "delivery_mechanism")
    op.drop_column("privacyexperienceconfighistory", "delivery_mechanism")

    op.drop_column("privacyexperienceconfig", "banner_title")
    op.drop_column("privacyexperienceconfig", "banner_description")
    op.drop_column("privacyexperienceconfig", "link_label")
    op.drop_column("privacyexperienceconfighistory", "banner_title")
    op.drop_column("privacyexperienceconfighistory", "banner_description")
    op.drop_column("privacyexperienceconfighistory", "link_label")

    op.add_column(
        "privacyexperienceconfig",
        sa.Column("banner_enabled", sa.String(), nullable=False),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("open_modal_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("privacy_policy_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("privacy_policy_url", sa.String(), nullable=True),
    )

    op.create_index(
        op.f("ix_privacyexperienceconfig_banner_enabled"),
        "privacyexperienceconfig",
        ["banner_enabled"],
        unique=False,
    )

    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("banner_enabled", sa.String(), nullable=False),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("open_modal_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("privacy_policy_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("privacy_policy_url", sa.String(), nullable=True),
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
        sa.Column(
            "banner_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("banner_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )

    op.drop_column("privacyexperienceconfighistory", "privacy_policy_url")
    op.drop_column("privacyexperienceconfighistory", "privacy_policy_label")
    op.drop_column("privacyexperienceconfighistory", "open_modal_label")
    op.drop_column("privacyexperienceconfighistory", "banner_enabled")
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
        sa.Column(
            "banner_description", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column("banner_title", sa.VARCHAR(), autoincrement=False, nullable=True),
    )

    op.drop_column("privacyexperienceconfig", "privacy_policy_url")
    op.drop_column("privacyexperienceconfig", "privacy_policy_label")
    op.drop_column("privacyexperienceconfig", "open_modal_label")
    op.drop_column("privacyexperienceconfig", "banner_enabled")
    op.add_column(
        "privacyexperience",
        sa.Column(
            "delivery_mechanism", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
    )
